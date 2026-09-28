# شروع پروژه Strategy Lab

این نسخهٔ اول نمونه‌کار آموزشی توست؛ هنوز PostgreSQL و LLM ندارد.

۱. فایل ZIP را استخراج کن و پوشهٔ strategy-lab را در VS Code باز کن.
۲. از منوی Terminal گزینهٔ New Terminal را بزن.
۳. با python --version نسخه را ببین؛ Python 3.11 یا بالاتر لازم است.
۴. مطابق README محیط مجازی را بساز و وابستگی‌ها را نصب کن.
۵. تست‌ها را با python -m pytest -q اجرا کن.
۶. سرور را با python -m uvicorn app.main:app --reload اجرا کن.
۷. در مرورگر http://127.0.0.1:8000/docs را باز کن.
۸. در POST /backtests گزینهٔ Try it out را بزن؛ محتوای examples/request.json را جایگزین کن و Execute را بزن.

اول app/models.py را بخوان: دادهٔ معتبر چه شرایطی دارد؟
بعد app/engine.py را بخوان: چرا سیگنال امروز در قیمت بازشدن کندل بعد اجرا می‌شود؟
سپس tests/test_backtest.py را بخوان: چطور با یک مثال دستی از محاسبات مطمئن می‌شویم؟

تمرین اول: کارمزد را از ۱۰ به ۳۰ تغییر بده و نتیجه را مقایسه کن.
تمرین دوم: fast_period را مساوی slow_period بگذار؛ خطای ۴۲۲ را بررسی کن.
تمرین سوم: آزمون دستی خرید در ۵ و فروش در ۱ را بدون کد محاسبه کن.

برای دریافت نسخهٔ مخزن، در ترمینال اجرا کن:

```bash
git clone https://github.com/CodeNomadSV/strategy-lab.git
cd strategy-lab
```

سپس مراحل ساخت محیط مجازی، نصب وابستگی‌ها و اجرای تست‌ها را از README انجام بده.
