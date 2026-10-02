"""Exercise the actual native card through its documented local bridge.

No news requests or AI generation are approved by this test. Test state is
isolated from the user's card. Screenshots are native card-host captures.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import shutil
import time
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--width', type=int, default=412)
parser.add_argument('--height', type=int, default=892)
parser.add_argument('--port', type=int, default=8170)
parser.add_argument('--bundle', type=Path, default=ROOT/'my-entry/morning-brief/bundle')
parser.add_argument('--baseline', action='store_true')
parser.add_argument('--news', action='store_true', help='offline native list/reader fixture; no provider requests')
parser.add_argument('--stress-ui', action='store_true', help='simulate voice controls and busy transcript for layout only')
parser.add_argument('--motion', action='store_true', help='verify finite opening and idle animation state')
parser.add_argument('--first-fold', action='store_true', help='primary preparation control is visible without scrolling')
parser.add_argument('--judging-ui', action='store_true', help='simulate returned editing perspectives for layout only')
args = parser.parse_args()
args.bundle = args.bundle.resolve()
bundle_bytes = sum(path.stat().st_size for path in args.bundle.rglob('*') if path.is_file())
assert bundle_bytes <= 8*1024*1024, f'bundle exceeds the official 8 MiB limit: {bundle_bytes}'
size = f'{args.width}x{args.height}'
folder = ROOT/'my-entry/evidence/ui-upgrade'/size
folder.mkdir(parents=True, exist_ok=True)
state = ROOT/'.local-state'/f'ui-qa-{size}'
if args.baseline:
    state = ROOT/'.local-state'/f'ui-baseline-{size}'
state.mkdir(parents=True, exist_ok=True)
if args.news:
    state = ROOT/'.local-state'/f'ui-news-{size}'
    (state/'morning-brief').mkdir(parents=True,exist_ok=True)
    fixture = ROOT/'.local-tools'/f'news-fixture-{size}'
    shutil.copytree(args.bundle,fixture,dirs_exist_ok=True)
    code = (fixture/'main.splash').read_text(encoding='utf-8')
    load_start = code.index('fn load_story(){')
    load_end = code.index('\nfn art_is_photo',load_start)
    code = code[:load_start]+'''fn load_story(){
    story_state = "ok"
    story_ai = "本地版式测试解读：这段文字用于验证中文长段落、换行和阅读滚动。\\n\\n" + story_sum
    art_on = true
    art_url = "{{assets}}/assets/editor-greeting.png"
    art_note = "本地角色素材，仅用于验证图片容器"
    sync_ui()
}
''' + code[load_end:]
    code = code.replace('fn art_kick(){','fn art_kick(){\n    return')
    start = code.index('fn row_img(r){')
    end = code.index('\nfn ', start+5)
    # The host expands asset tokens in script literals, not in persisted JSON.
    code = code[:start]+'fn row_img(r){ if r.id == "ui-demo-2" { return "{{assets}}/assets/editor-greeting.png" } "" }\n'+code[end:]
    for name in ('art_line','cover_line'):
        start = code.index(f'fn {name}(){{')
        end = code.index('\nfn ',start+5)
        code = code[:start]+f'fn {name}(){{ "本地 UI 素材，仅用于版式检查" }}\n'+code[end:]
    bootstrap = '''fn fixture_boot(){
    let payload = fs.read("ui_fixture.json").parse_json()
    picked = payload.rows
    last_rows = picked
    finished_at = time_now()
    cand_n = picked.len()
    ok_sources = payload.sources
    ai_intro = payload.intro
    phase = "done"
    cover_on = true
    cover_url = "{{assets}}/assets/editor-greeting.png"
    cover_head = "LOCAL PREVIEW · 本地版式测试"
    cover_state = "ok"
}
'''
    code = code.replace('fn boot(){',bootstrap+'\nfn boot(){')
    code = code.replace('    arc_load()\n    sync_ui()', '    arc_load()\n    fixture_boot()\n    sync_ui()')
    (fixture/'main.splash').write_text(code,encoding='utf-8',newline='\n')
    titles = [
        '本地测试：AI 开源技术的长标题阅读体验——从模型训练、推理成本、应用部署到读者最关心的实际变化，这是一条需要完整阅读而不能挤占全部屏幕的新闻标题',
        'Open-source AI agents: a deliberately long headline covering infrastructure, evaluation, deployment, and real-world reliability for the native reading layout',
        '本地测试：芯片与算力，三位编辑会怎样判断',
    ]
    rows = [{'id':f'ui-demo-{i}','title':title,'link':f'https://example.com/ui-fixture-{i}','source':'本地测试数据','published':int(time.time())-i*900,'summary':('这是独立的 UI 测试文字，不是当天新闻，也不是模型生成结果。用它检查段落、长标题、来源和滚动。\n\n'*8),'image':'','discussion':'','points':None,'comments':None} for i,title in enumerate(titles)]
    payload = {'rows':rows,'sources':[{'label':'本地 fixture','n':3}],'intro':'本页使用隔离的本地测试数据，检查头版、新闻列表、长标题与阅读排版。'}
    (state/'morning-brief/ui_fixture.json').write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
    (state/'morning-brief/ui_preferences.json').write_text('{"quiet":true}',encoding='utf-8')
    args.bundle = fixture
if args.stress_ui:
    state = ROOT/'.local-state'/f'ui-stress-{size}'
    state.mkdir(parents=True,exist_ok=True)
    fixture = ROOT/'.local-tools'/f'stress-fixture-{size}'
    shutil.copytree(args.bundle,fixture,dirs_exist_ok=True)
    code = (fixture/'main.splash').read_text(encoding='utf-8')
    code = code.replace('let vc_tts = false','let vc_tts = true').replace('let vc_stt = false','let vc_stt = true')
    code = code.replace('let ag_busy = false','let ag_busy = true')
    code = code.replace('let ag_log = []','let ag_log = [{who: "me" text: "本地测试消息"} {who: "ai" text: "仅验证版式，不调用模型。"} {who: "tool" text: "本地测试工具状态"}]')
    start = code.index('fn vc_probe(){')
    end = code.index('\nfn ',start+5)
    code = code[:start]+'fn vc_probe(){ vc_note = "本地 UI 测试：模拟双语音能力" sync_ui() }\n'+code[end:]
    (fixture/'main.splash').write_text(code,encoding='utf-8',newline='\n')
    args.bundle = fixture
if args.motion:
    state = ROOT/'.local-state'/f'ui-motion-{size}'
    (state/'morning-brief').mkdir(parents=True,exist_ok=True)
    (state/'morning-brief/ui_preferences.json').write_text('{"quiet":false}',encoding='utf-8')
if args.judging_ui:
    state=ROOT/'.local-state'/f'ui-judging-{size}'
    state.mkdir(parents=True,exist_ok=True)
    fixture=ROOT/'.local-tools'/f'judging-fixture-{size}'
    shutil.copytree(args.bundle,fixture,dirs_exist_ok=True)
    code=(fixture/'main.splash').read_text(encoding='utf-8')
    start=code.index('fn judge_line(){')
    end=code.index('\nfn ',start+5)
    code=code[:start]+'fn judge_line(){ "本地 UI 模拟 · 未调用模型" }\n'+code[end:]
    seed='''fn fixture_judging(){
        phase = "judging"
        cand_n = 3
        panel_state = "asking"
        panel_note = "本地 UI 布局测试，未调用模型"
        panel = [{id: "tech" label: "技术视角" state: "ok" votes: [0 1] ms: 2200 digest: "测试" model: "fixture"} {id: "biz" label: "行业视角" state: "fail" votes: [] ms: 0 digest: "测试" model: "fixture"}]
    }
'''
    code=code.replace('fn boot(){',seed+'\nfn boot(){').replace('    arc_load()\n    sync_ui()','    arc_load()\n    fixture_judging()\n    sync_ui()')
    (fixture/'main.splash').write_text(code,encoding='utf-8',newline='\n')
    args.bundle=fixture
env = dict(os.environ, MAKEPAD_REMOTE=str(args.port), MAKEPAD_HIDE_WINDOWS='1')
log_path = state/'card-host.log'
host = ROOT/'.local-tools/target/release/card-host.exe'

def request(route, **query):
    tail = '?' + urlencode(query) if query else ''
    with urlopen(f'http://127.0.0.1:{args.port}{route}{tail}', timeout=10) as response:
        return response.read()

def nodes():
    data = json.loads(request('/snap'))
    return [node for node in data.get('s', []) if node.get('ty') != 'Splash']

def button(label, exact=True):
    for node in nodes():
        if 'Button' in node.get('ty', '') and (node.get('t') == label if exact else label in node.get('t', '')):
            return node
    raise AssertionError(f'button missing: {label}')

def inside(node):
    x,y,w,h = node['r']
    return x >= -1 and y >= -1 and w > 0 and h > 0 and x+w <= args.width+1 and y+h <= args.height+1

def scroll_main(dy=160):
    current = nodes()
    box = next((node for name in ('story_content','list','decision_surface','browse') for node in current if node.get('i') == name and node['r'][3] > 0),None)
    assert box, 'active native scroller missing'
    x,y,w,h = box['r']
    request('/m',k='scroll',x=x+w/2,y=y+h/2,dx=0,dy=dy)

def click(label, exact=True):
    for turn in range(25):
        try: node = button(label, exact)
        except AssertionError: node = None
        if node and inside(node):
            x,y,w,h = node['r']
            request('/click', x=x+w/2, y=y+h/2, wait=1)
            return
        scroll_main()
        time.sleep(0.15)
    raise AssertionError(f'button missing or outside viewport: {label}: {node}')

def shot(name):
    path = folder/name
    data = request('/g', raw=1)
    assert data.startswith(b'\x89PNG'), 'bridge did not return PNG'
    path.write_bytes(data)
    (folder/(name+'.json')).write_text(json.dumps(nodes(),ensure_ascii=False,indent=2),encoding='utf-8')

def has(text):
    return any(node.get('t') == text for node in nodes())

def seek_text(text):
    for _ in range(10):
        found = next((node for node in nodes() if node.get('t') == text),None)
        if found and inside(found): return found
        scroll_main()
        time.sleep(0.1)
    raise AssertionError(f'text not reachable by scrolling: {text[:40]}')

with log_path.open('w', encoding='utf-8') as log:
    process = subprocess.Popen([str(host),'--bundle',str(args.bundle),'--app-data',str(state),'--allow-unsigned','--stamp','--size',size], cwd=ROOT/'OctoSense-App-Hub', env=env, stdout=log,stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic()+35
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(log_path.read_text(encoding='utf-8',errors='replace')[-5000:])
            try:
                if any(node.get('i') == 'ag_pill' and 'Button' in node.get('ty','') for node in nodes()):
                    break
            except OSError:
                pass
            time.sleep(0.25)
        else:
            raise AssertionError('native UI did not render before timeout')
        if args.motion:
            time.sleep(0.75)
            assert inside(button('跳过开场')), 'opening skip control missing'
            shot('10-opening-a.png')
            time.sleep(0.65)
            shot('11-opening-b.png')
            assert (folder/'10-opening-a.png').read_bytes() != (folder/'11-opening-b.png').read_bytes(), 'opening frames do not change'
            time.sleep(2.1)
            assert not any(node.get('t') == '跳过开场' for node in nodes()), 'opening did not end'
            assert 'animating=false' in log_path.read_text(encoding='utf-8',errors='replace'), 'idle still forces animation frame pump'
            shot('12-after-opening.png')
            print(f'PASS {size}: opening motion, skip affordance, automatic end, idle animation off')
        else: time.sleep(3.3)
        if args.motion:
            pass
        elif args.judging_ui:
            assert has('本地 UI 模拟 · 未调用模型'), 'fixture explanation is not visible'
            assert has('技术') and has('行业') and has('读者'), 'editing perspectives missing'
            assert has('推荐 2 条 · 2.2 秒') and has('未收到意见') and has('等待意见'), 'editing states do not match actual fixture values'
            assert has('初审编辑部 · 已返回 2 / 3 项结果'), 'returned results are misrepresented as successful opinions'
            shot('13-editorial-process.png')
            print(f'PASS {size}: simulated independent editing states and layout')
        elif args.stress_ui:
            assert inside(button('处理中')), 'busy footer control clipped'
            click('处理中')
            time.sleep(0.2)
            shot('09-voice-busy-ui.png')
            panel = next(node for node in nodes() if node.get('i') == 'ag_panel')
            send = button('发送')
            assert inside(send) and send['r'][1]+send['r'][3] <= panel['r'][1]+panel['r'][3]+1, 'voice controls push send outside editor panel'
            assert inside(button('朗读：开')), 'voice toggle clipped'
            transcript = next(node for node in nodes() if node.get('i') == 'ag_log_box')
            assert transcript['r'][3] >= 48 and has('本地测试消息'), 'voice controls collapse transcript'
            print(f'PASS {size}: simulated voice/busy controls and non-empty transcript bounds')
        elif args.news:
            shot('05-news-list-before.png')
            item = seek_text(titles[0])
            shot('05-news-list.png')
            x,y,w,h = item['r']
            request('/click',x=x+w/2,y=y+h/2,wait=1)
            time.sleep(0.3)
            assert has(titles[0]), 'reader did not open'
            shot('06-reader.png')
            click('打开主编')
            shot('07-reader-editor.png')
            content = next((node for node in nodes() if node.get('i') == 'story_content'),None)
            assert content and content['r'][3] >= 60, f'long headline collapsed reader body: {content}'
            assert inside(button('返回晨报')), 'reader back control clipped'
            click('收起主编')
            scroll_main(500)
            time.sleep(0.15)
            assert not any(node.get('i') == 'full_title' and inside(node) for node in nodes()), 'test did not actually scroll past the first headline'
            shot('07b-scrolled-reader.png')
            click('下一条')
            for _ in range(15):
                if has(titles[1]): break
                time.sleep(.05)
            else: raise AssertionError('next story did not open')
            headline = next((node for node in nodes() if node.get('i') == 'full_title'),None)
            content = next((node for node in nodes() if node.get('i') == 'story_content'),None)
            assert headline and content and headline.get('t') == titles[1] and headline['r'][1] >= content['r'][1]-1, 'next story did not reset to its headline'
            shot('08-next-story.png')
            click('返回晨报')
            assert has(titles[0]), 'reader did not return to news list'
            seek_text(titles[2])
            for _ in range(8):
                thumb = next((node for node in nodes() if node.get('i') == 'rth'),None)
                if thumb and inside(thumb): break
                scroll_main(80)
                time.sleep(.1)
            else: raise AssertionError('thumbnail row did not render within the native viewport')
            shot('14-thumbnail-row.png')
            print(f'PASS {size}: native offline list, long headline, editor, next story, back')
        elif args.baseline:
            footer = button('AI 主编', exact=False)
            shot('00-baseline.png')
            assert inside(footer), f'baseline main editor button clipped: {footer["r"]}'
            print('baseline footer bounds passed')
        else:
            assert inside(button('打开主编')), 'main editor entry is clipped'
            if args.first_fold:
                assert inside(button('准备今天的晨报')), 'primary preparation control is below first viewport'
            shot('01-home.png')
            click('+')
            assert has('11'), 'count increment failed'
            click('−')
            assert has('10'), 'count decrement failed'
            click('✓ AI')
            assert button('AI'), 'selected topic did not toggle off'
            click('AI')
            assert button('✓ AI'), 'topic did not toggle on'
            click('打开主编')
            assert has('AI 主编'), 'editor panel did not open'
            assert inside(button('发送')), 'editor send control is clipped'
            for _ in range(15):
                if any('告诉我你想关注什么' in node.get('t','') for node in nodes()): break
                time.sleep(0.1)
            else: raise AssertionError('editor empty guidance not rendered')
            shot('02-editor.png')
            click('收起主编')
            assert inside(button('打开主编')), 'editor panel did not close'
            click('准备今天的晨报')
            assert has('请确认这期取数计划'), 'plan not rendered'
            shot('03-plan.png')
            click('修改偏好')
            assert inside(button('准备今天的晨报')) and has('10') and button('✓ AI'), 'returning from plan lost preferences or the preparation control'
            click('准备今天的晨报')
            click('暂不取数')
            assert has('取数已取消'), 'deny did not preserve the no-fetch path'
            shot('04-denied.png')
            click('动效：', exact=False)
            preferences = json.loads((state/'morning-brief/ui_preferences.json').read_text(encoding='utf-8'))
            assert isinstance(preferences['quiet'], bool), 'motion preference not persisted'
            print(f'PASS {size}: footer bounds, count, topic, editor, plan, denial, motion preference')
        errors = log_path.read_text(encoding='utf-8',errors='replace')
        assert 'on_render closure failed' not in errors and 'callback error' not in errors, 'native callback failed; read log'
    finally:
        try: request('/quit')
        except OSError: pass
        try: process.wait(timeout=6)
        except subprocess.TimeoutExpired: process.terminate()
