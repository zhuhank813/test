"""Synthetic American football fourth-down laboratory. Python 3.10+, no dependencies."""
from pathlib import Path
import csv, random, math, json, html

ROOT = Path(__file__).resolve().parent
SEED = 813
rng = random.Random(SEED)

def probabilities(yards_to_goal, yards_to_go, skill=0):
    p = 1 / (1 + math.exp(-(.95 - .22 * yards_to_go + skill)))
    q = 1 / (1 + math.exp(-(5.7 - .105 * (yards_to_goal + 17))))
    return p, q

def values(y, d, skill=0):
    p, q = probabilities(y, d, skill)
    # Deliberately simplified possession-value units, NOT calibrated NFL EPA.
    success = 2 + 4 * (1-y/100)
    failure = -(1.2 + 2*y/100)
    kick_failure = -(0.6 + 1.6*y/100)
    punt = .3 - .008*y
    return {'GO':p*success+(1-p)*failure,
            'KICK':q*3+(1-q)*kick_failure, 'PUNT':punt}

def svg_start(title, subtitle, width=960, height=600):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="#0b1220"/><g font-family="Arial,sans-serif" fill="#edf3fc"><text x="40" y="45" font-size="26" font-weight="bold">{html.escape(title)}</text><text x="40" y="73" font-size="14" fill="#9cacc5">{html.escape(subtitle)}</text>'

def text(x,y,s,size=14,color='#edf3fc'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{html.escape(str(s))}</text>'

def save_svg(name, body):
    (ROOT/name).write_text(body+'</g></svg>', encoding='utf-8')

def main():
    teams = {f'Team {i+1:02d}':rng.gauss(0,.28) for i in range(16)}
    rows=[]
    for i in range(12000):
        team=rng.choice(list(teams)); y=rng.randint(10,90); d=rng.randint(1,15)
        p,q=probabilities(y,d,teams[team]); v=values(y,d,teams[team])
        # A noisy coach chooses the highest perceived value; selection is not random.
        a=max(v,key=lambda k:v[k]+rng.gauss(0,.7))
        prob = p if a=='GO' else q if a=='KICK' else None
        won=int(rng.random()<prob) if prob is not None else None
        realized=(2+4*(1-y/100) if won else -(1.2+2*y/100)) if a=='GO' else (3 if won else -(0.6+1.6*y/100)) if a=='KICK' else v[a]
        rows.append(dict(play_id=i+1,team=team,yards_to_goal=y,yards_to_go=d,action=a,
                         success_probability=prob,success=won,value=round(realized,4),
                         expected_value=round(v[a],4),optimal_action=max(v,key=v.get),
                         regret=round(max(v.values())-v[a],4)))
    with (ROOT/'synthetic_plays.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    assert len(rows)==12000 and all(r['regret']>=0 for r in rows)
    assert all(0 <= r['success_probability'] <= 1 for r in rows if r['success_probability'] is not None)
    colors={'GO':'#2dd4bf','KICK':'#fbbf24','PUNT':'#a78bfa'}
    body=svg_start('Fourth down: where does courage pay?', 'Toy model | Neutral team skill | Each cell selects the highest expected possession value')
    for d in range(1,16):
        for j,y in enumerate(range(10,91,5)):
            a=max(values(y,d),key=values(y,d).get)
            body+=f'<rect x="{100+j*45}" y="{105+(d-1)*26}" width="43" height="24" rx="3" fill="{colors[a]}"/>'
        body+=text(70,123+(d-1)*26,d)
    for j,y in enumerate(range(10,91,10)):body+=text(95+j*90,520,y)
    body+=text(100,553,'Yards to opponent end zone (further away →)')+text(40,99,'To go')
    for i,a in enumerate(colors):body+=f'<rect x="{590+i*110}" y="540" width="15" height="15" fill="{colors[a]}"/>'+text(610+i*110,553,a)
    save_svg('decision_map.svg',body)
    # Mean versus downside: exact two-point distributions, not estimated intervals.
    y,d=40,3;p,q=probabilities(y,d)
    distributions={'GO':[(p,4.4),(1-p,-2)],'KICK':[(q,3),(1-q,-1.24)],'PUNT':[(1,-.02)]}
    body=svg_start('The risk budget', 'At 40 yards to goal, 4th & 3 | Mean value and probability of a negative outcome',960,450)
    risk={}
    for i,(a,dist) in enumerate(distributions.items()):
        mu=sum(prob*x for prob,x in dist);neg=sum(prob for prob,x in dist if x<0)
        risk[a]={'expected_value':mu,'negative_probability':neg}
        yy=140+i*90;body+=text(40,yy,a,20,colors[a])
        body+=f'<rect x="170" y="{yy-25}" width="{max(mu,0)*160:.1f}" height="30" fill="{colors[a]}" rx="5"/>'
        body+=text(180+max(mu,0)*160,yy,f'{mu:+.2f} value')+text(640,yy,f'{neg:.1%} negative outcome',20)
    body+=text(40,410,'PUNT is deterministic in this toy model; its 100% negative rate means a tiny -0.02 value.')
    save_svg('risk_budget.svg',body)
    luck=[]
    for team in teams:
        go=[r for r in rows if r['team']==team and r['action']=='GO'];n=len(go)
        observed=sum(r['success'] for r in go)/n;expected=sum(r['success_probability'] for r in go)/n
        se=math.sqrt(sum(r['success_probability']*(1-r['success_probability']) for r in go))/n
        luck.append(dict(team=team,n=n,observed=observed,expected=expected,residual=observed-expected,se=se))
    luck.sort(key=lambda r:r['residual'])
    body=svg_start('Skill or a lucky season?', 'GO conversion rate minus known model probability | Bars are approximate ±1.96 standard errors',960,680)
    body+='<line x1="580" y1="100" x2="580" y2="600" stroke="#64748b"/>'
    for i,r in enumerate(luck):
        yy=120+i*29;x=580+r['residual']*2200;lo=x-1.96*r['se']*2200;hi=x+1.96*r['se']*2200
        body+=text(40,yy+5,f"{r['team']} (n={r['n']})")+f'<line x1="{lo}" y1="{yy}" x2="{hi}" y2="{yy}" stroke="#9cacc5" stroke-width="3"/><circle cx="{x}" cy="{yy}" r="6" fill="#2dd4bf"/>'
    for val in [-.1,-.05,0,.05,.1]:body+=text(565+val*2200,635,f'{val:+.0%}')
    save_svg('luck_meter.svg',body)
    match=sum(r['action']==r['optimal_action'] for r in rows)/len(rows)
    regret=sum(r['regret'] for r in rows)/len(rows)
    best=max(risk,key=lambda a:risk[a]['expected_value'])
    summary={'seed':SEED,'plays':len(rows),'policy_agreement':match,'mean_regret':regret,'scenario':risk,'teams':luck}
    (ROOT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    report=f'''# 第四檔決策實驗室：勇氣、風險與運氣

**全部數據均為 Python 生成的模擬美式橄欖球數據，並非 NFL 真實比賽資料。**

## 核心結果

- 16 支虛構球隊、12,000 次第四檔情境，固定亂數種子 {SEED}。
- 模擬教練有 {match:.1%} 的決策與模型的最高預期價值選項一致。
- 平均每次決策損失 {regret:.3f} 個模型價值單位：定義為最佳選項的預期價值減去實際選項的預期價值。
- 距達陣區 40 碼、第四檔需推進 3 碼時，最高預期價值選項為 **{best}**。

## 1. 勇氣地圖

![決策地圖](decision_map.svg)

GO = 強攻；KICK = 射門；PUNT = 棄踢。每格比較三種選項的預期價值。強攻成功率隨需推進碼數增加而下降；射門成功率隨距離增加而下降。這些模式是模型設計的結果，不能當成從真實聯盟發現的規律。

## 2. 高平均值不等於低風險

![風險預算](risk_budget.svg)

該情境的強攻預期價值為 {risk['GO']['expected_value']:.2f}，負值機率 {risk['GO']['negative_probability']:.1%}；射門預期價值為 {risk['KICK']['expected_value']:.2f}，負值機率 {risk['KICK']['negative_probability']:.1%}。圖中比較的是模型價值，不是得分或勝率。棄踢採固定 -0.02，因此雖有 100% 的負值機率，損失幅度很小；單看負值機率會誤導。

追分時是否應冒險，還需要剩餘時間、分差與勝率模型。本實驗只展示均值與風險的差異，不對追分戰術作結論。

## 3. 運氣濾鏡

![運氣指標](luck_meter.svg)

每隊實際強攻成功率減去每次情境的已知成功機率平均值，將情境難度和模型球隊能力納入基準。誤差棒為條件於這些機率的約 95% 常態區間，16 隊比較未做多重比較修正。殘差不是能力排名；它只量化這次模擬中隨機結果的偏離。真实資料沒有已知機率，需要另建並驗證預測模型。

## 模型與限制

- 強攻成功機率：sigmoid(0.95 - 0.22 × 需推進碼數 + 球隊能力)。球隊能力從 N(0, 0.28²) 生成。
- 射門成功機率：sigmoid(5.7 - 0.105 × (距達陣區碼數 + 17))；17 碼是此實驗假設。
- 若 y 為距達陣區碼數，強攻成功价值 = 2 + 4(1-y/100)，失敗 = -(1.2+2y/100)；射門成功 = 3，失敗 = -(0.6+1.6y/100)；棄踢 = 0.3-0.008y。
- 這些手工設定的價值是示範單位，沒有經過 NFL EPA 校準，也不含真正的後續攻防序列。
- 教練在各選項價值加入 N(0, 0.7²) 雜訊後選最大值；直接比較各選項的觀察平均值會受選擇偏差影響。
- 無時間、分差、天氣、防守、傷病或棄踢波動；不是教練實戰建議。
- 程式包含資料筆數、機率範圍與非負 regret 檢查。

## 重跑

```bash
python analysis.py
```

Python 3.10 或以上，無第三方套件。程式會在自身所在目錄重新生成 CSV、JSON、三張 SVG 圖、Markdown 與 HTML 報告。CSV 空白的 success / success_probability 代表棄踢情境不適用。
'''
    (ROOT/'REPORT.md').write_text(report,encoding='utf-8')
    # Self-contained HTML with inline SVG, usable offline without web libraries.
    chunks=[]
    for line in report.splitlines():
        if line.startswith('!['):
            filename=line.split('](')[1][:-1];chunks.append((ROOT/filename).read_text(encoding='utf-8'));continue
        if line.startswith('# '):chunks.append('<h1>'+html.escape(line[2:])+'</h1>')
        elif line.startswith('## '):chunks.append('<h2>'+html.escape(line[3:])+'</h2>')
        elif line and not line.startswith('```'):chunks.append('<p>'+html.escape(line)+'</p>')
    (ROOT/'report.html').write_text('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>第四檔決策實驗室</title><style>body{max-width:1050px;margin:40px auto;padding:24px;background:#0b1220;color:#edf3fc;font:17px/1.8 system-ui}h1,h2{color:#2dd4bf}svg{width:100%;height:auto;border:1px solid #25334a;border-radius:12px;margin:15px 0}p{color:#ced8e7}</style>'+''.join(chunks)+'</html>',encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ['plays','policy_agreement','mean_regret','scenario']},indent=2))

if __name__=='__main__':main()
