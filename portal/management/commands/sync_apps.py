"""
Django Management Command: sync_apps
從 apps.json 檔案讀取子應用模組清單，並批次同步/更新至資料庫。
支援安全 Upsert（以 app_id 為唯一識別鍵）。
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from portal.models import AppModule

logger = logging.getLogger(__name__)


def resolve_apps_json_path(custom_path: Optional[str] = None) -> Optional[Path]:
    """
    解析 apps.json 的檔案路徑：
    1. 自訂路徑 (custom_path)
    2. settings.DATA_DIR / 'apps.json' (Docker 掛載目錄)
    3. settings.BASE_DIR / 'apps.json' (專案根目錄)
    """
    if custom_path:
        p = Path(custom_path)
        return p if p.is_file() else None

    # 檢查 DATA_DIR (若有設定且存在)
    data_dir = getattr(settings, 'DATA_DIR', None)
    if data_dir:
        data_json = Path(data_dir) / 'apps.json'
        if data_json.is_file():
            return data_json

    # 檢查 BASE_DIR
    base_json = Path(settings.BASE_DIR) / 'apps.json'
    if base_json.is_file():
        return base_json

    return None


def sync_apps_from_json(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    執行 JSON 同步至 AppModule 資料庫：
    - Safe Upsert：根據 app_id 更新或新增
    - 不刪除未列在 JSON 內的現有專案
    """
    resolved = resolve_apps_json_path(file_path)
    if not resolved:
        target = file_path or f"{getattr(settings, 'DATA_DIR', settings.BASE_DIR)}/apps.json"
        return {
            'success': False,
            'error': f'找不到 apps.json 檔案 (查找目標: {target})',
            'created': 0,
            'updated': 0,
            'total': 0,
            'file_path': None
        }

    try:
        with open(resolved, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'JSON 格式解析失敗 ({resolved.name}): {e}',
            'created': 0,
            'updated': 0,
            'total': 0,
            'file_path': str(resolved)
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'讀取檔案失敗 ({resolved}): {e}',
            'created': 0,
            'updated': 0,
            'total': 0,
            'file_path': str(resolved)
        }

    if not isinstance(data, list):
        return {
            'success': False,
            'error': f'JSON 格式錯誤：最外層應為應用模組清單陣列 (List/Array)，目前型態為 {type(data).__name__}',
            'created': 0,
            'updated': 0,
            'total': 0,
            'file_path': str(resolved)
        }

    created_count = 0
    updated_count = 0
    errors = []

    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            errors.append(f"第 {index} 筆項目格式無效（應為物件/字典）")
            continue

        app_id = str(item.get('app_id', '')).strip()
        if not app_id:
            errors.append(f"第 {index} 筆項目缺少必要欄位 'app_id'")
            continue

        name_zh = item.get('name_zh', '').strip()
        name_en = item.get('name_en', '').strip()
        route_path = item.get('route_path', '').strip()

        if not name_zh or not route_path:
            errors.append(f"專案 [{app_id}] 缺少必要欄位 'name_zh' 或 'route_path'")
            continue

        defaults = {
            'icon': item.get('icon', '🚀'),
            'name_zh': name_zh,
            'name_en': name_en or name_zh,
            'description_zh': item.get('description_zh', ''),
            'description_en': item.get('description_en', ''),
            'category': item.get('category', 'other'),
            'route_path': route_path,
            'target_port': int(item.get('target_port', 8000)),
            'status': item.get('status', 'active'),
            'is_new': bool(item.get('is_new', False)),
            'is_active': bool(item.get('is_active', True)),
            'display_order': int(item.get('display_order', index)),
        }

        obj, is_created = AppModule.objects.update_or_create(
            app_id=app_id,
            defaults=defaults
        )
        if is_created:
            created_count += 1
        else:
            updated_count += 1

    return {
        'success': len(errors) == 0 or (created_count + updated_count > 0),
        'file_path': str(resolved),
        'created': created_count,
        'updated': updated_count,
        'total': len(data),
        'errors': errors
    }


class Command(BaseCommand):
    help = 'Batch sync dynamic app modules from apps.json into database (Safe Upsert)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Specify apps.json file path (defaults to DATA_DIR / BASE_DIR)'
        )
        parser.add_argument(
            '--silent-if-missing',
            action='store_true',
            help='Do not error if apps.json is missing, silently skip'
        )

    def handle(self, *args, **options):
        custom_file = options.get('file')
        silent_if_missing = options.get('silent_if_missing', False)

        result = sync_apps_from_json(custom_file)

        if not result['success']:
            if not result['file_path'] and (silent_if_missing or not custom_file):
                self.stdout.write(self.style.WARNING(f"[NOTICE] apps.json not found; skipping dynamic apps sync."))
                return
            raise CommandError(result.get('error', 'Failed to sync apps.json'))

        self.stdout.write(
            self.style.SUCCESS(
                f"[SUCCESS] Synced apps from {result['file_path']}: "
                f"{result['created']} created, {result['updated']} updated, {result['total']} processed."
            )
        )

        if result.get('errors'):
            for err in result['errors']:
                self.stdout.write(self.style.WARNING(f"[WARNING] {err}"))
