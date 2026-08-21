# مشکلات راه‌اندازی در ویندوز {#windows-startup-issues}

<!-- toc -->

## بدون خطا، اما برنامه ظاهر نمی‌شود {#no-error-but-app-does-not-appear}

اگر آنکی را شروع می‌کنید و بدون هیچ پیام خطایی ظاهر نمی‌شود، می‌توانید موارد زیر را امتحان کنید:

- نمایشگرهای چندگانه/خارجی را جدا کنید.
- [آخرین نسخه آنکی](https://apps.ankiweb.net/) را نصب کنید.
- اگر جداکننده اعشار شما نقطه نیست، [جداکننده اعشار](https://forums.ankiweb.net/t/windows-update-broke-anki/1822/75)‌تان را تنظیم کنید.
- بیلد قدیمی [2.1.35-alternate](https://github.com/ankitects/anki/releases/tag/2.1.35) آنکی را نصب کنید.

## به‌روزرسانی‌های ویندوز {#windows-updates}

هنگام شروع آنکی ممکن است پیام‌هایی مانند زیر بگیرید:

- _Error loading Python DLL_
- _The program can't start because api-ms-win.... is missing_
- _Failed to execute script runanki_
- _Failed to execute script pyi_rth_multiprocessing_
- _Failed to execute script pyi_rth_win32comgenpy_

این خطاها معمولاً به‌دلیل نبود به‌روزرسانی یا کتابخانه ویندوزی روی رایانه شماست.

Windows update را باز کنید و مطمئن شوید سیستم‌تان همه به‌روزرسانی‌ها را نصب دارد.
اگر چیزی لازم بود نصب شود، پس از نصب، دستگاه‌تان را دوباره راه‌اندازی کنید.

## ویندوز ۷/۸ {#windows-78}

در ویندوز ۷/۸، شاید لازم باشد به‌طور دستی به‌روزرسانی‌های اضافی نصب کنید. امتحان کنید:

- <https://www.microsoft.com/en-us/download/details.aspx?id=48234>
- <https://aka.ms/vs/15/release/vc_redist.x64.exe>
- <http://www.catalog.update.microsoft.com/Search.aspx?q=kb4474419>
- <http://www.catalog.update.microsoft.com/Search.aspx?q=kb4490628>

## مشکلات درایور ویدیو {#video-driver-issues}

لطفاً [مشکلات نمایش](./display-issues.md) را ببینید.

## نمایشگرهای چندگانه {#multiple-displays}

اگر خطای _LoadLibrary failed with error 126_ می‌گیرید، این ممکن است به‌دلیل مشکل جعبه‌ابداری که آنکی روی آن ساخته شده با [نمایشگرهای چندگانه](https://forums.ankiweb.net/t/error-126-on-open-anki-desktop/13967) باشد.

## نرم‌افزار آنتی‌ویروس/فایروال {#antivirusfirewall-software}

نرم‌افزار شخص ثالثی روی رایانه شما ممکن است مانع بارگیری آنکی شود. می‌توانید برای آنکی استثنا بگذارید، یا آنتی‌ویروس/فایروال‌تان را موقتاً غیرفعال کنید تا ببینید کمک می‌کند یا نه.

## دسترسی مدیر {#admin-access}

بعضی کاربران گزارش کرده‌اند که آنکی برایشان اجرا نشد تا اینکه روی نشان آنکی راست‌کلیک کردند و "Run as administrator" را انتخاب کردند. آنکی همه داده‌هایش را در پوشه کاربری شما ذخیره می‌کند و نباید به امتیازات مدیر نیاز داشته باشد، اما چیزی است که می‌توانید در صورت پایان یافتن گزینه‌های دیگر امتحان کنید.

## چند نصب آنکی پس از به‌روزرسانی {#multiple-anki-installations-present-after-updating}

اگر فرایند به‌روزرسانی چند نصب آنکی برایتان به جا بگذارد (مثلاً درون
`C:\Program Files\Anki` و `C:\Program Files (x86)\Anki`)، ممکن است در وضعیت غیرکارآمدی مانده باشند و آنکی بدون نمایش پیام خطا از شروع سر باز بزند.

همه رونوشت‌های آنکی را از رایانه‌تان حذف کنید. برای این کار، آن‌ها را در Windows Settings > Apps & features (یا Apps > Installed apps) بیابید و حذف کنید، یا `uninstall.exe` را در هر پوشه برنامه آنکی اجرا کنید. پس از آن، آنکی را دوباره نصب کنید.

## اشکال‌زدایی {#debugging}

شروع آنکی از ترمینال ممکن است کمی اطلاعات بیشتر درباره بعضی خطاها آشکار کند. پس از نصب آخرین نسخه آنکی و مطمئن‌شدن از نصب همه به‌روزرسانی‌های ویندوز، به‌جای اجرای مستقیم آنکی، کلید <kbd>Windows</kbd> را بزنید (یا منوی Start را باز کنید)، `cmd` را تایپ کنید و Command Prompt را اجرا کنید. وقتی پنجره ترمینال باز شد، دستور زیر را بچسبانید و <kbd>Enter</kbd> را بزنید. (مسیر متفاوت خواهد بود اگر آنکی در مکانی غیر از پیش‌فرض نصب شده باشد.)

```
%LocalAppData%\Programs\Anki\anki-console.bat
```

برای نسخه‌های 25.07 تا 25.09.4 آنکی، این را بچسبانید

```
%LocalAppData%\Programs\Anki\anki-console.exe
```

احتمالاً آنکی مثل قبل باز نمی‌شود، اما خروجی پنجره ترمینال ممکن است چیزی درباره علت مشکل آشکار کند.

## اگر هیچ‌کدام جواب نداد {#if-all-else-fails}

اگر پس از امتحان راه‌حل‌های بالا نتوانستید آنکی را شروع کنید، دو گزینه پیش روی شماست:

- می‌توانید [اجرا از Python](https://faqs.ankiweb.net/running-from-python.html) را امتحان کنید.
- می‌توانید نسخه قدیمی‌تر آنکی ساخته‌شده با جعبه‌ابزار قدیمی‌تر را امتحان کنید؛ مانند
  [2.1.35-alternate](https://github.com/ankitects/anki/releases/tag/2.1.35) یا [2.1.15](https://github.com/ankitects/anki/releases/tag/2.1.15).
