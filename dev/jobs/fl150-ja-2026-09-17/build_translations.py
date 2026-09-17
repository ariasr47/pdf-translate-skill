# Builds translations.json and fills widget_text.json for the FL-150 -> ja job.
# Merges are declared by segment id and their exact texts are read from
# segments.json, so nothing is re-typed. Every core must be covered; the
# script fails loudly on an unknown core or an unused key.
import json, sys

import os
W = os.path.dirname(os.path.abspath(__file__))
segs = json.load(open(f"{W}/segments.json", encoding="utf-8"))["segments"]
cores = [c["text"] for c in json.load(open(f"{W}/to_translate.json", encoding="utf-8"))["cores"]]
by_id = {g["id"]: g for g in segs}

SP = "（記入）："      # (specify):
EX = "（説明）："      # (explain):

T = {
 # footer / header identity block: kept verbatim, as the issuer does in its own translations
 "Page 1 of 4": "第1ページ／全4ページ",
 "Page 2 of 4": "第2ページ／全4ページ",
 "Page 3 of 4": "第3ページ／全4ページ",
 "Page 4 of 4": "第4ページ／全4ページ",
 "Form Adopted for Mandatory Use": "Form Adopted for Mandatory Use",
 "Judicial Council of California": "Judicial Council of California",
 "FL-150 [Rev. September 1, 2024]": "FL-150 [Rev. September 1, 2024]",
 "INCOME AND EXPENSE DECLARATION": "収入・支出申告書",
 "Family Code, §§ 2030–2032, 2100–2113,": "Family Code, §§ 2030–2032, 2100–2113,",
 "www.courts.ca.gov": "www.courts.ca.gov",
 "FL-150": "FL-150",
 "FL-150 INCOME AND EXPENSE DECLARATION": "FL-150 収入・支出申告書",

 # caption block
 "PARTY WITHOUT ATTORNEY OR ATTORNEY": "弁護士を立てない当事者または弁護士",
 "STATE BAR NUMBER:": "州弁護士会番号：",
 "NAME:": "氏名：",
 "FIRM NAME:": "事務所名：",
 "STREET ADDRESS:": "住所：",
 "CITY:": "市：",
 "STATE:": "州：",
 "ZIP CODE:": "郵便番号：",
 "TELEPHONE NO.:": "電話番号：",
 "FAX NO.:": "FAX番号：",
 "E-MAIL ADDRESS:": "メールアドレス：",
 "ATTORNEY FOR (name):": "（氏名）の代理人弁護士：",
 "SUPERIOR COURT OF CALIFORNIA, COUNTY OF": "カリフォルニア州上位裁判所、郡：",
 "MAILING ADDRESS:": "郵送先住所：",
 "CITY AND ZIP CODE:": "市・郵便番号：",
 "BRANCH NAME:": "支部名：",
 "PETITIONER:": "申立人：",
 "RESPONDENT:": "相手方：",
 "OTHER PARTY/PARENT/CLAIMANT:": "その他の当事者／親／請求人：",
 "FOR COURT USE ONLY": "裁判所記入欄",
 "CASE NUMBER:": "事件番号：",

 # 1. employment
 "Employment (Give information on your current job or, if you're unemployed, your most recent job.)":
   "雇用‖（現在の仕事、無職の場合は直近の仕事について記入してください。）",
 "Attach copies": None, "of your pay": None, "stubs for last": None, "two months": None,
 "(black out": None, "Social": None, "Security": None, "numbers).": None,
 "Employer:": "勤務先：",
 "Employer's address:": "勤務先住所：",
 "Employer's phone number:": "勤務先電話番号：",
 "Occupation:": "職業：",
 "Date job started:": "就職日：",
 "If unemployed, date job ended:": "無職の場合、退職日：",
 "I work about": "私は週に約",
 "hours per week.": "時間働いています。",
 "I get paid $": "給与額 $",
 "per month": "月給",
 "per week": "週給",
 "per hour.": "時給",
 "gross (before taxes)": "総額（税引前）",
 "(If you have more than one job, attach an 8 1/2-by-11-inch sheet of paper and list the same information as above for your other": None,
 "jobs. Write \"Question 1—Other Jobs\" at the top.)": None,

 # 2. age and education
 "Age and education": "年齢と学歴",
 "My age is (specify):": "年齢" + SP,
 "I have completed high school or the equivalent:": "高校または同等の課程を修了しています：",
 "Yes": "はい",
 "No": "いいえ",
 "If no, highest grade completed (specify):": "（いいえの場合）最終修了学年" + SP,
 "Number of years of college completed (specify):": "大学の修了年数" + SP,
 "Degree(s) obtained (specify):": "取得学位" + SP,
 "Number of years of graduate school completed (specify):": "大学院の修了年数" + SP,
 "I have:": "資格等：",
 "professional/occupational license(s) (specify):": "専門職・職業免許" + SP,
 "vocational training (specify):": "職業訓練" + SP,

 # 3. tax
 "Tax information": "税務情報",
 "I last filed taxes for tax year (specify year):": "最後に申告した課税年度（年を記入）：",
 "My tax filing status is": "納税申告区分：",
 "single": "独身",
 "head of household": "特定世帯主",
 "married, filing separately": "夫婦個別申告",
 "married, filing jointly with (specify name):": "夫婦合算申告（配偶者名を記入）：",
 "I file state tax returns in": "州税の申告先：",
 "California": "カリフォルニア",
 "other (specify state):": "その他（州名）：",
 "I claim the following number of exemptions (including myself) on my taxes (specify):":
   "納税申告における控除対象人数（本人を含む）" + SP,

 # 4. other party
 "Other party's income. I estimate the gross monthly income (before taxes) of the other party in this case at (specify): $":
   "相手方の収入。‖本件の相手方の月間総収入（税引前）を次の額と推定します" + SP + "$",
 "This estimate is based on (explain):": "この推定の根拠" + EX,
 "(If you need more space to answer any questions on this form, attach an 8 1/2-by-11-inch sheet of paper and write the": None,
 "question number before your answer.)": None,
 "Number of pages attached:": "添付ページ数：",
 "I declare under penalty of perjury under the laws of the State of California that the information contained on all pages of this form and": None,
 "any attachments is true and correct.": None,
 "Date:": "日付：",
 "(TYPE OR PRINT NAME)": "（氏名を活字体で記入）",
 "(SIGNATURE OF DECLARANT)": "（申告者の署名）",

 # page 2
 "Attach copies of your pay stubs for the last two months and proof of any other income. Take a copy of your latest federal tax": None,
 "return to the court hearing. (Black out your Social Security number on the pay stub and tax return.)": None,
 "Income (For average monthly, add up all the income you received in each category in the last 12 months": None,
 "and divide the total by 12.)": None,
 "Last month": "先月",
 "Average": None,
 "monthly": None,
 "Salary or wages (gross, before taxes)": "給与または賃金（総額、税引前）",
 "Overtime (gross, before taxes)": "残業手当（総額、税引前）",
 "Commissions or bonuses": "歩合給または賞与",
 "Public assistance (for example: TANF, SSI, GA/GR)": None,
 "currently receiving": "現在受給中",
 "Spousal support": "配偶者扶養料",
 "from this marriage": "本件の婚姻から",
 "from a different marriage": "別の婚姻から",
 "federally taxable*": "連邦課税対象*",
 "Partner support": "パートナー扶養料",
 "from this domestic partnership": "本件の登録パートナーシップから",
 "from a different domestic partnership": "別の登録パートナーシップから",
 "Pension/retirement fund payments": "年金・退職基金からの支給",
 "Social Security retirement (not SSI)": "社会保障退職年金（SSIを除く）",
 "Disability:": "障害給付：",
 "Social Security (not SSI)": "社会保障（SSIを除く）",
 "State disability (SDI)": "州障害保険（SDI）",
 "Private insurance": "民間保険",
 "Unemployment compensation": "失業給付",
 "Workers' compensation": "労災補償",
 "Other (military allowances, royalty payments) (specify):": "その他（軍人手当、ロイヤルティ等）" + SP,
 "Investment income (Attach a schedule showing gross receipts less cash expenses for each piece of property.)":
   "投資収入‖（各資産について、総収入から現金支出を差し引いた明細表を添付してください。）",
 "Dividends/interest": "配当・利息",
 "Rental property income": "不動産賃貸収入",
 "Trust income": "信託収入",
 "Other (specify):": "その他" + SP,
 "Income from self-employment, after business expenses for all businesses": "自営業収入（全事業の事業経費控除後）",
 "I am the": "私の立場：",
 "owner/sole proprietor": "所有者／個人事業主",
 "business partner": "共同経営者",
 "other (specify):": "その他：",
 "Number of years in this business (specify):": "この事業の経営年数" + SP,
 "Name of business (specify):": "事業名" + SP,
 "Type of business (specify):": "事業の種類" + SP,
 "Attach a profit and loss statement for the last two years or a Schedule C from your last federal tax return. Black out your": None,
 "Social Security number. If you have more than one business, provide the information above for each of your businesses.": None,
 "Additional income. I received one-time money (lottery winnings, inheritance, etc.) in the last 12 months (specify source and": None,
 "amount):": None,
 "Change in income. My financial situation has changed significantly over the last 12 months because (specify):":
   "収入の変化。‖過去12か月間に私の経済状況は次の理由で大きく変化しました" + SP,
 "Deductions": "控除",
 "Required union dues": "義務的な組合費",
 "Required retirement payments (not Social Security, FICA, 401(k), or IRA)": "義務的な退職年金掛金（社会保障、FICA、401(k)、IRAを除く）",
 "Medical, hospital, dental, and other health insurance premiums (total monthly amount)": "医療・入院・歯科・その他の健康保険料（月額合計）",
 "Child support that I pay for children from other relationships": "他の関係の子のために支払っている養育費",
 "Spousal support that I pay by court order from a different marriage": None,
 "federally tax deductible*": "連邦税控除対象*",
 "Partner support that I pay by court order from a different domestic partnership": "別の登録パートナーシップについて裁判所命令により支払っているパートナー扶養料",
 "Necessary job-related expenses not reimbursed by my employer (attach explanation labeled \"Question 10g\")":
   "雇用主から払い戻されない必要な業務関連費用（「Question 10g」と題した説明を添付）",
 "Assets": "資産",
 "Total": "合計",
 "Cash and checking accounts, savings, credit union, money market, and other deposit accounts": "現金、当座預金、普通預金、信用組合、マネーマーケット口座、その他の預金口座",
 "Stocks, bonds, and other assets I could easily sell": "株式、債券、その他容易に売却できる資産",
 "real    and": None,
 "personal": "動産",
 "* Check the box if the spousal support order or judgment was executed by the parties and the court before January 1, 2019, or if a court-ordered change": None,
 "maintains the spousal support payments as taxable income to the recipient and tax deductible to the payor.": None,

 # page 3
 "The following people live with me:": "次の人が私と同居しています：",
 "Name": "氏名",
 "Age": "年齢",
 "How the person is": None, "related to me (ex: son)": None,
 "That person's gross": None, "monthly income": None,
 "Pays some of the": None, "household expenses?": None,
 "Average monthly expenses": "月平均支出",
 "Estimated expenses": "見積支出",
 "Actual expenses": "実際の支出",
 "Proposed needs": "今後必要な額",
 "Home:": "住居：",
 "Rent     or": None,
 "mortgage": "住宅ローン",
 "If mortgage:": "住宅ローンの場合：",
 "average principal:": "平均元本：",
 "average interest:": "平均利息：",
 "Real property taxes": "固定資産税",
 "Homeowner's or renter's insurance": "住宅所有者保険または借家人保険",
 "(if not included above)": "（上記に含まれない場合）",
 "Maintenance and repair": "維持・修繕費",
 "Health-care costs not paid by insurance": "保険でカバーされない医療費",
 "Child care": "保育費",
 "Groceries and household supplies": "食料品・日用品",
 "Eating out": "外食費",
 "Utilities (gas, electric, water, trash)": "水道光熱費（ガス、電気、水道、ごみ）",
 "Telephone, cell phone, and e-mail": "電話・携帯電話・メール",
 "Laundry and cleaning": "洗濯・クリーニング",
 "Clothes": "衣服費",
 "Education": "教育費",
 "Entertainment, gifts, and vacation": "娯楽・贈答・旅行",
 "Auto expenses and transportation": "自動車費・交通費",
 "(insurance, gas, repairs, bus, etc.)": "（保険、ガソリン、修理、バス等）",
 "Insurance (life, accident, etc.; do not include": "保険（生命、傷害等。自動車、住宅、",
 "auto, home, or health insurance)": "医療保険は含めない）",
 "Savings and investments": "貯蓄・投資",
 "Charitable contributions": "寄付金",
 "Monthly payments listed in item 14": "14に記載の月々の支払",
 "(itemize below in 14 and insert total here)": "（14に内訳を記入し、合計をここに記入）",
 "TOTAL EXPENSES (a–q) (do not add in": "支出合計‖（a–q）（次を加算しないこと：",
 "the amounts in a(1)(a) and (b))": "a(1)(a)と(b)の金額）",
 "Amount of expenses paid by others": "他者が支払った支出の額",
 "Paid to": "支払先",
 "Installment payments and debts not listed above": "上記以外の分割払いおよび債務",
 "For": "用途",
 "Amount": "金額",
 "Balance": "残高",
 "Date of last payment": "最終支払日",
 "Attorney fees (This information is required if either party is requesting attorney fees):":
   "弁護士費用‖（いずれかの当事者が弁護士費用を請求する場合は必須）：",
 "To date, I have paid my attorney this amount for fees and costs (specify): $": "これまでに弁護士に支払った報酬と費用の額" + SP + "$",
 "The source of this money was (specify):": "この資金の出所" + SP,
 "I still owe the following fees and costs to my attorney (specify total owed): $": "弁護士に対する未払いの報酬と費用（未払総額を記入）：$",
 "My attorney's hourly rate is (specify):": "弁護士の時間当たり料金" + SP,
 "I confirm this fee arrangement.": "私はこの報酬取決めを確認します。",
 "(TYPE OR PRINT NAME OF ATTORNEY)": "（弁護士の氏名を活字体で記入）",
 "(SIGNATURE OF ATTORNEY)": "（弁護士の署名）",

 # page 4
 "CHILD SUPPORT INFORMATION": "子の養育費に関する情報",
 "(NOTE: Fill out this page only if your case involves child support.)": "（注：子の養育費が関係する場合のみ記入してください。）",
 "Children's health-care expenses": "子の医療費",
 "I do": "あり",
 "I do not": "なし",
 "have health insurance available to me for the children through my job.": "勤務先を通じて子のために利用できる健康保険",
 "Name of insurance company:": "保険会社名：",
 "Address of insurance company:": "保険会社の住所：",
 "The monthly cost for the children's health insurance is or would be (specify): $": "子の健康保険の月額費用（現在または見込み）" + SP + "$",
 "(Do not include the amount your employer pays.)": "（雇用主が負担する額は含めないこと。）",
 "Number of children": "子の人数",
 "I have (specify number):": "私には（人数を記入）：",
 "children under the age of 18 with the other parent in this case.": "人の18歳未満の子が本件の他方の親との間にいます。",
 "The children spend": "子は私と",
 "percent of their time with me and": "％、他方の親と",
 "percent of their time with the other parent.": "％の時間を過ごします。",
 "(If you're not sure about percentage or it has not been agreed on, please describe your parenting schedule here.)":
   "（割合が不明な場合や合意していない場合は、ここに養育スケジュールを記述してください。）",
 "Additional expense for the children in this case": "本件の子に関する追加費用",
 "Childcare so I can work or get job training": "就労または職業訓練のための保育費",
 "Children's health care not covered by insurance": "保険適用外の子の医療費",
 "Travel expenses for visitation": "面会交流のための交通費",
 "Children's educational or other special needs (specify below):": "子の教育上その他の特別なニーズ（下に記入）：",
 "Amount per month": "月額",
 "Special hardships. I ask the court to consider the following special financial circumstances":
   "特別な困窮事情。‖裁判所に次の特別な経済的事情の考慮を求めます",
 "(attach documentation of any item listed here, including court orders):": "（記載項目の証拠書類（裁判所命令を含む）を添付）：",
 "For how many months?": "何か月間？",
 "Extraordinary health expenses not included in 18b": "18bに含まれない多額の医療費",
 "Major losses not covered by insurance (examples: fire, theft, other": "保険適用外の重大な損失（例：火災、盗難、",
 "insured loss)": "その他の損失）",
 "Expenses for my minor children who are from other relationships and": "他の関係から生まれ、私と同居している",
 "are living with me": "未成年の子の費用",
 "Names and ages of those children (specify):": "その子らの氏名と年齢" + SP,
 "Child support I receive for those children": "その子らのために受け取っている養育費",
 "The expenses listed in a, b, and c create an extreme financial hardship because (explain):": "a、b、cの費用が極度の経済的困窮をもたらす理由" + EX,
 "Other information I want the court to know concerning support in my case (specify):": "本件の養育費・扶養料に関して裁判所に知らせたいその他の情報" + SP,
}

# the one core whose text carries a long run of spaces: key it from the extractor's own list
all_other = [c for c in cores if c.startswith("All other property,")]
assert len(all_other) == 1, all_other
T[all_other[0]] = None

missing = [c for c in cores if c not in T]
unused = [k for k in T if k not in cores]
if missing or unused:
    print("MISSING:", missing); print("UNUSED:", unused); sys.exit(1)

def lines(ids):
    return [by_id[i]["text"] for i in ids]

merges = [
 {"page": 0, "lines": lines([33, 34, 35, 36, 37, 38, 39, 40]),
  "html": "直近2か月分の給与明細の写しを添付してください（社会保障番号は黒塗り）。", "align": "left", "box": None},
 {"page": 0, "lines": lines([56, 57]),
  "html": "<b>（仕事が複数ある場合は、8 1/2×11インチの用紙を添付し、他の仕事についても上記と同じ情報を記載してください。用紙の上部に「Question 1—Other Jobs」と書いてください。）</b>",
  "align": "left", "box": None},
 {"page": 0, "lines": lines([89, 90]),
  "html": "<b>（回答欄が足りない場合は、8 1/2×11インチの用紙を添付し、回答の前に質問番号を書いてください。）</b>",
  "align": "left", "box": None},
 {"page": 0, "lines": lines([92, 93]),
  "html": "私は、カリフォルニア州法に基づく偽証罪の罰則の下で、本書式の全ページおよび添付書類に記載した情報が真実かつ正確であることを宣言します。",
  "align": "left", "box": None},
 {"page": 1, "lines": lines([105, 106]),
  "html": "<b>直近2か月分の給与明細の写しと、その他の収入の証明を添付してください。審問には直近の連邦所得税申告書の写しを持参してください。（給与明細と申告書の社会保障番号は黒塗りにしてください。）</b>",
  "align": "left", "box": None},
 {"page": 1, "lines": lines([108, 109]),
  "html": "<b>収入</b>（月平均は、過去12か月間に各項目で受け取った収入をすべて合計し、12で割ってください。）",
  "align": "left", "box": None},
 {"page": 1, "lines": lines([111, 112]), "html": "月平均", "align": "center", "box": [527.0, 146.5, 567.0, 158.7]},
 {"page": 1, "lines": lines([170, 171]),
  "html": "<b>過去2年分の損益計算書、または直近の連邦所得税申告書の Schedule C を添付してください。社会保障番号は黒塗りにしてください。事業が複数ある場合は、各事業について上記の情報を記載してください。</b>",
  "align": "left", "box": None},
 {"page": 1, "lines": lines([173, 174]),
  "html": "<b>追加収入。</b>過去12か月間に一時金（宝くじの当選金、相続等）を受け取りました（出所と金額を記入）：",
  "align": "left", "box": None},
 {"page": 1, "lines": lines([202, 203]),
  "html": "* 配偶者扶養料の命令または判決が2019年1月1日より前に当事者および裁判所によって署名・成立した場合、または裁判所命令による変更により配偶者扶養料が受取人の課税所得かつ支払人の税控除対象のままである場合は、このボックスにチェックしてください。",
  "align": "left", "box": None},
 {"page": 2, "lines": lines([215, 216]), "html": "続柄（例：息子）", "align": "left", "box": None},
 {"page": 2, "lines": lines([217, 218]), "html": "その人の月間総収入", "align": "left", "box": None},
 {"page": 2, "lines": lines([219, 220]), "html": "家計費の一部を<br>負担していますか？", "align": "left", "box": None},
]

overrides = [
 {"page": 1, "contains": "Public assistance (for example",
  "parts": [{"text": "d.", "x": 50.9},
            {"text": "公的扶助（例：TANF、SSI、GA/GR）", "x": 65.6},
            {"text": "." * 34, "x": 382.8}]},
 {"page": 1, "contains": "Spousal support that I pay by court order",
  "parts": [{"text": "別の婚姻について裁判所命令により支払っている配偶者扶養料", "x": 65.8},
            {"text": "." * 26, "x": 454.5}]},
 {"page": 1, "contains": "All other property,",
  "parts": [{"text": "その他の全財産、", "x": 65.6},
            {"text": "（公正市場価格から負債を差し引いた推定額）", "x": 296.7},
            {"text": "." * 16, "x": 478.5}]},
 {"page": 1, "contains": "real    and",
  "parts": [{"text": "不動産", "x": 167.1}, {"text": "および", "x": 197.0}]},
 {"page": 2, "contains": "Rent     or",
  "parts": [{"text": "家賃", "x": 104.6}, {"text": "または", "x": 130.0}]},
]

NOTICE = ("【参考訳】裁判所には提出できません。‖"
          "これは「FL-150 INCOME AND EXPENSE DECLARATION」の非公式な日本語訳で、書式の内容を理解するためのものです。"
          "裁判所には正式な英語版の書式に記入して提出してください。両者に相違がある場合は、英語版が優先します。")

out = {
 "fonts": {"regular": "font-regular.ttf", "bold": "font-bold.ttf"},
 "lang": "ja",
 "translations": {c: T[c] for c in cores},
 "merges": merges,
 "center": ["INCOME AND EXPENSE DECLARATION", "FOR COURT USE ONLY", "Last month", "Total",
            "CHILD SUPPORT INFORMATION",
            "(NOTE: Fill out this page only if your case involves child support.)",
            "Amount per month", "For how many months?"],
 "right": ["PETITIONER:", "RESPONDENT:", "OTHER PARTY/PARENT/CLAIMANT:", "STATE BAR NUMBER:",
           "STATE:", "ZIP CODE:", "FAX NO.:", "Page 1 of 4", "Page 2 of 4", "Page 3 of 4", "Page 4 of 4"],
 "skip": [],
 "allow_scale": [],
 "notices": [{"page": 0, "text": NOTICE, "box": [412.0, 152.0, 573.0, 216.0], "size": 7, "bold_lead": True}],
 "overrides": overrides,
}
json.dump(out, open(f"{W}/translations.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("translations.json:", len(cores), "cores,", sum(1 for c in cores if T[c] is None), "null (merge/override-covered),",
      len(merges), "merges,", len(overrides), "overrides")

# widget text: tooltips reuse the page labels; the few tooltip-only strings are listed here
EXTRA = {
 "Number of hours per week that I work": "週の労働時間数",
 "Degree(s) obtained": "取得学位",
 "(specify):": SP,
 "vocational training": "職業訓練",
 "other": "その他",
 "Average monthly": "月平均",
 "Specify source and amount": "出所と金額を記入",
 "real and": "不動産",
 "$": "$",
 "How the person is related to me (ex: son)": "私との続柄（例：息子）",
 "That person's gross monthly income": "その人の月間総収入",
 "Additional income. I received one-time money (lottery winnings, inheritance, etc.) in the last 12 months (specify source and amount):":
   "追加収入。過去12か月間に一時金（宝くじの当選金、相続等）を受け取りました（出所と金額を記入）：",
 "Public assistance (for example: TANF, SSI, GA/GR)": "公的扶助（例：TANF、SSI、GA/GR）",
 "Spousal support that I pay by court order from a different marriage": "別の婚姻について裁判所命令により支払っている配偶者扶養料",
}
wt_path = f"{W}/widget_text.json"
wt = json.load(open(wt_path, encoding="utf-8"))
unresolved = []
for name, spec in wt.items():
    for key in ("tooltip", "default", "value"):
        if key in spec and isinstance(spec[key], dict):
            src = spec[key]["source"]
            tgt = EXTRA.get(src, T.get(src))
            if tgt is None:
                unresolved.append((name, key, src)); continue
            spec[key]["target"] = tgt.replace("‖", "")
    if "options" in spec:
        unresolved.append((name, "options", spec["options"]))
if unresolved:
    print("UNRESOLVED widget text:", unresolved); sys.exit(1)
json.dump(wt, open(wt_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("widget_text.json: all", len(wt), "targets authored")
