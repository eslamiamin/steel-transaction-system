import streamlit as st
import jdatetime
import json
import re
from decimal import Decimal, getcontext
getcontext().prec=50
from database_v1 import get_connection, read_data
import pandas as pd
st.set_page_config(page_title='فولاد جهان',layout='wide')
st.markdown("""<style>
[data-testid="stMainBlockContainer"]{direction:rtl;text-align:right;max-width:1200px;padding:2rem 2.5rem 4rem}
#MainMenu,[data-testid="stMainMenu"],[data-testid="stAppDeployButton"],.stAppDeployButton{display:none!important}
[data-testid="stSidebar"]{background:#101e30;direction:rtl;text-align:right}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] a{color:#f1e7d5}
[data-testid="stSidebar"] [data-baseweb="select"] > div{background:#243b55!important;color:#ffffff!important;border-color:#d8b477!important}
[data-testid="stSidebar"] [data-baseweb="select"] *,[data-testid="stSidebar"] [data-baseweb="select"] input{color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;fill:#ffffff!important}
[data-baseweb="popover"] [role="listbox"],[data-baseweb="popover"] [role="option"]{background:#ffffff;color:#101e30!important}
[data-baseweb="popover"] [role="option"]:hover{background:#e9edf3!important}
[data-baseweb="popover"] [role="option"] *{color:#101e30!important}
[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{color:#172b4d!important}
[data-testid="stSidebarCollapsedControl"] svg,[data-testid="collapsedControl"] svg{fill:currentColor!important}
[data-testid="stSidebar"] a[aria-current="page"]{background:#263b56;border-radius:8px}
h1,h2,h3{color:#172b4d} h1{font-size:2rem!important} h3{font-size:1.05rem!important}
[data-testid="stMetric"]{background:#fff;border:1px solid #e1e6ed;border-top:3px solid #d8b477;border-radius:12px;padding:16px}
[data-testid="stMetricValue"]{direction:ltr;text-align:right;font-size:1.45rem}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:14px!important}
[data-testid="stTextInput"] input{ text-align:right }
[data-testid="stButton"] button[kind="primary"]{background:#172b4d;color:white;border:1px solid #172b4d;min-height:48px;border-radius:9px}
[data-testid="stButton"] button[kind="primary"]:hover{background:#294566;color:white}
</style>""",unsafe_allow_html=True)
masters={'SupplierID':('Suppliers','SupplierName'),'ProductID':('Products','ProductName'),'UnitID':('Units','UnitName'),'SellerID':('Sellers','SellerName'),'CustomerID':('CustomersV2','CustomerName'),'PurchaseTypeID':('PurchaseTypes','TypeName'),'SettlementID':('SettlementTypes','SettlementName')}
labels={'SupplierID':'تامین کننده','ProductID':'کالا','UnitID':'واحد','SellerID':'فروشنده مسئول','CustomerID':'مشتری','PurchaseTypeID':'نوع معامله','SettlementID':'تسویه'}
def mapping(k):
    t,n=masters[k]; return {int(a):b for a,b in read_data(f'SELECT {k},{n} FROM dbo.{t} '+(' WHERE IsActive=1' if t in ('Suppliers','Products') else '')+f' ORDER BY {n}').itertuples(index=False,name=None)}
def choose(k,old=None,scope=""):
    if k=="ProductID":
        df=rows("SELECT p.ProductID,p.ProductName,p.SizeName,p.IsActive,c.CategoryName,s.SubcategoryName FROM dbo.Products p LEFT JOIN dbo.ProductSubcategories s ON s.SubcategoryID=p.SubcategoryID LEFT JOIN dbo.ProductCategories c ON c.CategoryID=s.CategoryID")
        df=df[(df.IsActive==1)|(df.ProductID==old)] .fillna("تعریف نشده")
        for field,label in [("CategoryName","دسته اصلی"),("SubcategoryName","زیرگروه"),("SizeName","اندازه")]:
            opts=sorted(df[field].unique()); prior=df.loc[df.ProductID==old,field].tolist(); selected=st.selectbox(label,opts,index=opts.index(prior[0]) if prior and prior[0] in opts else None,key=scope+field); df=df[df[field]==selected]
        m=dict(zip(df.ProductID,df.ProductName)); ids=list(m); return st.selectbox("کالا",ids,index=ids.index(old) if old in ids else None,format_func=m.get,key=scope+k)
    m=mapping(k)
    if k=="PurchaseTypeID":
        m={i:n for i,n in m.items() if str(n).strip().replace("ي","ی").replace("‌"," ") in ("بورسی","غیر بورسی","غیربورسی")}
        if old is not None and int(old) not in m:
            st.warning("نوع معامله قبلی باید با یکی از انواع جدید جایگزین شود.")
    ids=list(m)
    if not ids: st.error('اطلاعات پایه ناقص است: '+labels[k]); st.stop()
    return st.selectbox(labels[k],ids,index=ids.index(int(old)) if old is not None and int(old) in ids else None,format_func=m.get,key=scope+k)
def rows(sql): return read_data(sql)
def parse_jalali(value):
    value=value.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789'))
    if not re.fullmatch(r'[0-9]{4}/[0-9]{2}/[0-9]{2}',value):
        raise ValueError('تاریخ باید دقیقاً به شکل 1405/09/04 باشد')
    return jdatetime.date(*map(int,value.split('/')))
def date_hint(value):
    if value:
        try: parse_jalali(value)
        except ValueError: st.error('تاریخ نامعتبر؛ فرمت صحیح: 1405/09/04')
def jalali(d): return jdatetime.date.fromgregorian(date=d).strftime('%Y/%m/%d')
P='PurchasesV4'; S='SalesV4'
base='SELECT p.*, s.SupplierName, g.ProductName,u.UnitName, p.TotalQuantity-COALESCE(x.Sold,0) AS Remaining FROM dbo.PurchasesV4 p JOIN dbo.Suppliers s ON s.SupplierID=p.SupplierID JOIN dbo.Products g ON g.ProductID=p.ProductID JOIN dbo.Units u ON u.UnitID=p.UnitID OUTER APPLY(SELECT SUM(TotalQuantity) Sold FROM dbo.SalesV4 WHERE PurchaseID=p.PurchaseID)x'
def persist(table,values,old,actor,reason):
    conn=get_connection()
    try:
        c=conn.cursor(); pid=int(values['PurchaseID']) if table==S else (int(old['PurchaseID']) if old is not None else None)
        if pid is not None:
            c.execute('SELECT TotalQuantity,InvoiceDate FROM dbo.PurchasesV4 WITH (UPDLOCK,HOLDLOCK) WHERE PurchaseID=?',pid); parent=c.fetchone()
            if parent is None: raise ValueError('خرید یافت نشد')
            c.execute('SELECT COALESCE(SUM(TotalQuantity),0),MIN(InvoiceDate) FROM dbo.SalesV4 WHERE PurchaseID=? AND SaleID<>?',pid,int(old['SaleID']) if table==S and old is not None else -1); sold,first=c.fetchone()
            if table==S and (sold+(values['Quantity']+(values['Quantity2'] or 0))>parent[0] or values['InvoiceDate']<parent[1]): raise ValueError('مقدار بیش از مانده یا تاریخ فروش قبل از خرید است')
            if table==P and ((values['Quantity']+(values['Quantity2'] or 0))<sold or (first and values['InvoiceDate']>first)): raise ValueError('اصلاح با فروش‌های ثبت شده ناسازگار است')
            if table==P and sold and any(values[k]!=old[k] for k in ['ProductID','UnitID']): raise ValueError('کالا و واحد خرید دارای فروش قابل تغییر نیست')
        pk='PurchaseID' if table==P else 'SaleID'
        if old is None:
            c.execute(f'INSERT dbo.{table} ('+','.join(values)+f') OUTPUT INSERTED.{pk} VALUES ('+','.join('?' for _ in values)+')',*values.values()); rid=c.fetchone()[0]
        else:
            rid=int(old[pk]); c.execute(f'UPDATE dbo.{table} SET '+','.join(k+'=?' for k in values)+f' WHERE {pk}=? AND Version=?',*values.values(),rid,bytes(old['Version']))
            if c.rowcount!=1: raise ValueError('رکورد همزمان تغییر کرده؛ دوباره انتخاب کنید')
            c.execute('INSERT dbo.AuditV4(Entity,RecordID,ActorID,Reason,OldData,NewData) VALUES(?,?,?,?,?,?)',table,rid,actor,reason,json.dumps({k:old[k] for k in values},default=str,ensure_ascii=False),json.dumps(values,default=str,ensure_ascii=False))
        conn.commit(); return rid
    except Exception: conn.rollback(); raise
    finally: conn.close()
def editor(table,old=None,parent=None):
    def v(k,d=None): return old[k] if old is not None else d
    scope=f'{table}_{v("PurchaseID" if table==P else "SaleID",parent or "new")}_'
    values={}
    raw_notes=str(v('Notes')) if pd.notna(v('Notes')) else ''
    prefix='[تاریخ تسویه: '
    old_settle=''
    if raw_notes.startswith(prefix) and ']\n' in raw_notes:
        old_settle,raw_notes=raw_notes[len(prefix):].split(']\n',1)
    with st.container(border=True):
        st.markdown('### ۱. اطلاعات فاکتور')
        a,b,c=st.columns(3)
        with a: values['ManualInvoiceNo']=st.text_input('شماره فاکتور دفتری',str(v('ManualInvoiceNo')) if pd.notna(v('ManualInvoiceNo')) else '',max_chars=50,key=scope+'manual')
        with b:
            date=st.text_input('تاریخ شمسی',jalali(v('InvoiceDate')) if old is not None else jdatetime.date.today().strftime('%Y/%m/%d'),max_chars=10,key=scope+'date')
            date_hint(date)
        with c: values['SellerID']=choose('SellerID',v('SellerID'),scope)
        a,b=st.columns(2)
        party='SupplierID' if table==P else 'CustomerID'
        with a: values[party]=choose(party,v(party),scope)
        with b: values['PurchaseTypeID']=choose('PurchaseTypeID',v('PurchaseTypeID'),scope)
    if table==P:
        with st.container(border=True):
            st.markdown('### ۲. مشخصات کالا')
            a,b=st.columns([3,1])
            with a: values['ProductID']=choose('ProductID',v('ProductID'),scope)
            with b: values['UnitID']=choose('UnitID',v('UnitID'),scope)
    with st.container(border=True):
        st.markdown('### مقدار و قیمت')
        dual=st.checkbox('دو نرخی',value=old is not None and pd.notna(v('Quantity2')),key=scope+'dual')
        a,b=st.columns(2)
        qty=a.text_input('مقدار',str(v('Quantity','')),key=scope+'qty'); rate=b.text_input('فی اول',str(v('Rate','')),key=scope+'rate')
        q2=r2=None
        if dual:
            a,b=st.columns(2)
            q2=a.text_input('مقدار دوم',str(v('Quantity2')) if pd.notna(v('Quantity2')) else '',key=scope+'q2')
            r2=b.text_input('فی دوم',str(v('Rate2')) if pd.notna(v('Rate2')) else '',key=scope+'r2')
    with st.container(border=True):
        st.markdown('### تسویه و توضیحات')
        a,b=st.columns(2)
        with a: values['SettlementID']=choose('SettlementID',v('SettlementID'),scope)
        with b:
            settlement_date=st.text_input('تاریخ تسویه (شمسی)',old_settle,placeholder='1405/09/04',max_chars=10,key=scope+'settledate')
            date_hint(settlement_date)
        notes=st.text_area('توضیحات',raw_notes,max_chars=2000,key=scope+'notes')
        values['Notes']=notes
    try:
        q=Decimal(qty)+(Decimal(q2) if dual else 0); amount=Decimal(qty)*Decimal(rate)+(Decimal(q2)*Decimal(r2) if dual else 0)
        if q.is_finite() and amount.is_finite():
            metrics=st.columns(4 if table==S else 2); metrics[0].metric('مقدار کل',f'{q:,.3f}'); metrics[1].metric('مبلغ کل',f'{amount:,.2f}')
            if table==S:
                p=rows(f'SELECT TotalAmount,TotalQuantity FROM dbo.PurchasesV4 WHERE PurchaseID={int(parent)}').iloc[0]
                cost=q*Decimal(str(p.TotalAmount))/Decimal(str(p.TotalQuantity)); metrics[2].metric('مبلغ خرید متناظر',f'{cost:,.2f}'); metrics[3].metric('مابه‌التفاوت',f'{amount-cost:,.2f}')
    except (ArithmeticError,ValueError): pass
    reason=st.text_input('دلیل اصلاح',max_chars=500) if old is not None else ''
    if st.button('ثبت اصلاح' if old is not None else 'ثبت نهایی فاکتور',type='primary',use_container_width=True):
        try:
            if any(x is None for x in values.values()): raise ValueError('تمام گزینه‌ها را انتخاب کنید')
            values['InvoiceDate']=parse_jalali(date).togregorian()
            if settlement_date.strip():
                sd=parse_jalali(settlement_date)
                values['Notes']=prefix+sd.strftime('%Y/%m/%d')+']\n'+notes
            if len(values['Notes'].encode('utf-16-le'))//2>2000: raise ValueError('مجموع توضیحات و تاریخ تسویه بیش از ظرفیت مجاز است')
            for k,t,scale in [('Quantity',qty,3),('Rate',rate,2),('Quantity2',q2,3),('Rate2',r2,2)]:
                n=Decimal(t) if t is not None else None
                if n is not None and (not n.is_finite() or n<0 or n>=10**(18-scale) or n!=n.quantize(Decimal(10)**-scale)): raise ValueError('عدد نامعتبر است')
                values[k]=n
            if values['Quantity']<=0 or (dual and values['Quantity2']<=0): raise ValueError('مقدار باید مثبت باشد')
            if table==S: values['PurchaseID']=int(parent)
            if not values['ManualInvoiceNo'].strip(): raise ValueError('شماره فاکتور دفتری الزامی است')
            if old is not None and not reason.strip(): raise ValueError('دلیل اصلاح الزامی است')
            rid=persist(table,values,old,actor,reason); st.success(f'ثبت موفق | شماره {rid:06d}')
        except Exception as e: st.error(str(e))
def pick_purchase(open_only=False):
    df=rows(base+(' WHERE p.TotalQuantity>COALESCE(x.Sold,0)' if open_only else '')); m={int(r.PurchaseID):f'{r.PurchaseID:06d} | {r.ProductName} | {r.SupplierName} | مانده {r.Remaining}' for r in df.itertuples()}; return st.selectbox('فاکتور خرید',list(m),index=None,format_func=m.get)
try:
    actor=st.sidebar.selectbox('کاربر ثبت‌کننده اصلاحات',list(mapping('SellerID')),format_func=mapping('SellerID').get)
except Exception: st.error('ابتدا setup_v4.sql را در دیتابیس اجرا کنید'); st.stop()
def purchase():
    st.title('ثبت فاکتور خرید'); editor(P)
def sale():
    st.title('ثبت فاکتور فروش'); pid=pick_purchase(True)
    if pid is not None:
        st.dataframe(rows(base+f' WHERE p.PurchaseID={int(pid)}').drop(columns=['Version']),hide_index=True)
        editor(S,parent=pid)
def opened():
    st.title('خریدها و مانده کالا'); st.dataframe(rows(base).drop(columns=['Version']),hide_index=True)
def report():
    st.title('گزارش معاملات'); df=rows('''SELECT p.PurchaseID AS [شماره فاکتور],s.SaleID AS [شماره فروش],g.ProductName AS [کالا],v.SupplierName AS [خرید از],c.CustomerName AS [مشتری],p.InvoiceDate AS [تاریخ خرید],s.InvoiceDate AS [تاریخ فروش],t.SettlementName AS [تسویه],u.UnitName AS [واحد],s.TotalQuantity AS [مقدار],p.TotalAmount/NULLIF(p.TotalQuantity,0) AS [فی خرید],s.TotalAmount/NULLIF(s.TotalQuantity,0) AS [فی فروش],s.TotalQuantity*(p.TotalAmount/NULLIF(p.TotalQuantity,0)) AS [مبلغ خرید],s.TotalAmount AS [مبلغ فروش],s.TotalAmount-s.TotalQuantity*(p.TotalAmount/NULLIF(p.TotalQuantity,0)) AS [مابه التفاوت],a.SellerName AS [فروشنده],p.ManualInvoiceNo AS [دفتری خرید],s.ManualInvoiceNo AS [دفتری فروش],p.Notes AS [توضیحات خرید],s.Notes AS [توضیحات فروش] FROM dbo.SalesV4 s JOIN dbo.PurchasesV4 p ON p.PurchaseID=s.PurchaseID JOIN dbo.Products g ON g.ProductID=p.ProductID JOIN dbo.Suppliers v ON v.SupplierID=p.SupplierID JOIN dbo.CustomersV2 c ON c.CustomerID=s.CustomerID JOIN dbo.SettlementTypes t ON t.SettlementID=s.SettlementID JOIN dbo.Units u ON u.UnitID=p.UnitID JOIN dbo.Sellers a ON a.SellerID=s.SellerID ORDER BY s.SaleID DESC''');
    for k in ['تاریخ خرید','تاریخ فروش']: df[k]=df[k].map(jalali)
    st.dataframe(df,hide_index=True); st.download_button('خروجی CSV',df.to_csv(index=False).encode('utf-8-sig'),'report.csv')
def edit():
    st.title('اصلاح فاکتور'); table=st.radio('نوع',['خرید','فروش'],horizontal=True); table=P if table=='خرید' else S; pk='PurchaseID' if table==P else 'SaleID'; df=rows(f'SELECT * FROM dbo.{table}'); rid=st.selectbox('شماره',df[pk].tolist(),index=None)
    if rid is not None:
        old=df[df[pk]==rid].iloc[0]
        with st.container():
            editor(table,old,old['PurchaseID'] if table==S else None)
def audit():
    st.title('تاریخچه اصلاحات'); st.dataframe(rows('SELECT a.*,s.SellerName FROM dbo.AuditV4 a JOIN dbo.Sellers s ON s.SellerID=a.ActorID ORDER BY AuditID DESC'),hide_index=True)
def master():
    st.title('اطلاعات پایه'); k=st.selectbox('نوع اطلاعات',list(masters),format_func=labels.get); t,n=masters[k]; st.dataframe(rows(f'SELECT * FROM dbo.{t}'),hide_index=True); st.caption('مدیریت اطلاعات در SSMS انجام می‌شود.'); st.dataframe(rows('SELECT * FROM dbo.Services'),hide_index=True)
st.navigation([st.Page(f,title=t,url_path=u) for f,t,u in [(purchase,'ثبت خرید','purchase'),(sale,'ثبت فروش','sale'),(opened,'مانده خرید','open'),(report,'گزارش معاملات','report'),(edit,'اصلاح فاکتور','edit'),(audit,'تاریخچه اصلاحات','audit'),(master,'اطلاعات پایه','master')]]).run()
