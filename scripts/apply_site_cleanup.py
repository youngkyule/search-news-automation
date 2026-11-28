"""라벨 통일(consolidate_labels)과 소개·문의·개인정보 페이지 갱신(update_static_pages)을 한 번에 실행한다.
--apply 가 없으면 라벨은 dry-run만 하고 페이지는 건드리지 않는다."""
import runpy
import sys
from pathlib import Path

here = Path(__file__).parent
sys.path.insert(0, str(here))
runpy.run_path(str(here / "consolidate_labels.py"), run_name="__main__")
if "--apply" in sys.argv:
    import update_static_pages

    update_static_pages.main()
