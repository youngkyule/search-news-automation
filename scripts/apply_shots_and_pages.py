"""화면 캡처 삽입(add_screenshots)과 소개·문의·개인정보 페이지 갱신(update_static_pages)을 한 번에 실행한다."""
import runpy
import sys
from pathlib import Path

here = Path(__file__).parent
sys.path.insert(0, str(here))
runpy.run_path(str(here / "add_screenshots.py"), run_name="__main__")
if "--apply" in sys.argv:
    import update_static_pages

    update_static_pages.main()
