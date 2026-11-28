"""data/image_plan.json의 글 순서를 기준으로 Flow 이미지 프롬프트(data/flow_prompts.md)와
매니페스트(data/flow_manifest.json)를 만든다."""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
P = {
1: ("hands filling out an online form on a laptop at a tidy home desk, cardboard moving boxes blurred in the background", "apartment entrance hallway with house keys on a shelf and stacked moving boxes"),
2: ("adult learners with laptops in a bright modern classroom, instructor at whiteboard, faces not shown", "hands taking notes beside a training textbook and a laptop on a desk"),
3: ("laptop on a desk with a loading spinner on the screen, no readable text", "hands typing on a laptop with many browser tabs open, screen content blurred"),
4: ("two cars after a minor collision on a quiet city street in daylight, no people", "hand holding a smartphone photographing a dented car bumper"),
5: ("row of used cars in a sunny dealership lot", "person inspecting the engine bay of a used car with a flashlight, face not shown"),
6: ("study desk with exam textbooks, highlighter and laptop, warm light", "hands holding a blank professional certificate document"),
7: ("cardboard parcels stacked at an apartment doorstep", "hands opening a shipping box on a table with a paper receipt"),
8: ("leather wallet with several credit cards partly pulled out on a wooden table, no readable numbers", "hand holding a smartphone with a blurred banking app next to a credit card"),
9: ("clean bright white bathroom toilet area", "rubber gloves, toilet brush and a spray bottle with baking soda on a bathroom tile floor"),
10: ("city intersection with traffic lights and two cars stopped after an accident, daylight, no close-up people", "dashboard camera mounted on a windshield looking at a busy road"),
11: ("calculator, loan paperwork and pen on a desk", "small house model with keys and coins on a table"),
12: ("neatly made white bed with soft morning sunlight", "vacuum cleaner cleaning a mattress with bedding beside it"),
13: ("formal legal documents with a fountain pen on a desk", "courthouse building exterior with steps in daylight"),
14: ("young office worker on first day at a desk with notebook and laptop, face not shown", "two colleagues shaking hands in a modern bright office"),
15: ("student studying at a library desk with a stack of books", "hands writing in a notebook with a timer on a desk"),
16: ("hand holding a smartphone with generic blurred chat bubbles", "external hard drive and smartphone connected by cable on a desk"),
17: ("home printer printing documents in a tidy office", "stack of official paper documents with a stamp on a desk"),
18: ("job seeker browsing listings on a laptop in a cafe, face not shown", "folder of documents and a resume on a desk beside coffee"),
19: ("woman working on a laptop at a home kitchen table, natural light", "professional woman in a blazer walking toward an office building, seen from behind"),
20: ("person measuring blood pressure with a wrist cuff monitor", "glass of water and fresh fruit on a desk in morning light"),
21: ("wooden hair comb and brush on a bathroom counter", "person rubbing temples at a desk, seen from behind"),
22: ("cup of herbal tea next to a light meal of soup and rice", "person resting on a sofa holding their stomach, seen from the side, face not shown"),
23: ("glass of water, fruit and oatmeal breakfast on a table in morning light", "person walking on a park path in the morning, seen from behind"),
24: ("laptop with an online shopping cart and a parcel return box on a desk", "customer service headset on a clean desk"),
25: ("tissue box with tissues on a bedside table", "humidifier releasing mist in a bedroom"),
26: ("printed certificate document and pen on an office desk", "employee ID badge on a lanyard lying on a desk"),
27: ("wifi router with glowing lights on a shelf", "laptop at a home desk with a router in the background"),
28: ("hand holding a generic smartphone viewing a photo gallery, no logos", "smartphone and memory cards on a desk representing storage"),
29: ("laptop showing a plain blue error screen with no readable text on a desk", "technician repairing the inside of a desktop PC, face not shown"),
30: ("front-loading washing machine in a tidy laundry room with the door open", "laundry detergent and a basket of clean towels"),
31: ("smartphone charging on a wooden table with a cable", "smartphone resting on a metal cooling stand on a desk"),
32: ("legal documents and pen under a desk lamp", "police station building entrance in daylight"),
33: ("car dashboard with illuminated warning lights, no brand logos", "mechanic checking a car with a diagnostic tablet, face not shown"),
34: ("bright living room with clean white curtains and sunlight", "hands folding clean curtain fabric next to a laundry basket"),
35: ("car parked on a street with a parking violation notice on the windshield", "no parking road sign on a city street"),
36: ("apartment keys and a rental contract on a table", "apartment building exterior in daylight"),
37: ("neat shoe cabinet in a home entrance", "sneakers being cleaned with a brush on a newspaper"),
38: ("resume, pen and laptop on a desk", "job interview table with two chairs in a bright office"),
39: ("highway toll gate with cars passing", "car driving on an expressway through a toll lane"),
}
SUF = ". Photorealistic editorial photograph, natural light, 16:9 landscape, sharp detail, no text, no logos, no watermark."

plan = json.load(open(ROOT / "data" / "image_plan.json", encoding="utf8"))
assert len(plan) == len(P), (len(plan), len(P))
man, md = [], ["# Flow 이미지 프롬프트\n\n"
    "사용법: Google Flow에서 아래 영어 프롬프트로 이미지를 생성하고(가로 16:9), 마음에 드는 것을 아래 파일명으로 저장해 `assets/blog/` 폴더에 넣으세요.\n"
    "- 파일명: `01-1.jpg`, `01-2.jpg` (글 번호-순번). png도 가능하지만 jpg 권장.\n"
    "- 얼굴이 뚜렷하게 나오거나 글자·로고가 보이는 이미지는 피하세요.\n"]
for i, p in enumerate(plan, 1):
    prompts = [x + SUF for x in P[i]]
    man.append(dict(idx=i, url=p["url"], title=p["title"], prompts=prompts))
    md.append(f"\n## {i:02d}. {p['title']}\n")
    for k, t in enumerate(prompts, 1):
        md.append(f"- `{i:02d}-{k}.jpg`: {t}\n")
json.dump(man, open(ROOT / "data" / "flow_manifest.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
(ROOT / "data" / "flow_prompts.md").write_text("".join(md), encoding="utf8")
print(len(man), "글 처리")
