# مشکلات نمایش در macOS {#display-issues-on-macos}

<!-- toc -->

## تغییر درایور ویدیو {#change-the-video-driver}

### تغییر درایور از صفحه تنظیمات {#changing-the-driver-from-the-preferences-screen}
اگر در آنکی 23.10+ مشکلات نمایش یا خرابی دارید، می‌توانید با رفتن به **Anki →
Preferences** و سپس انتخاب درایور از فهرست کشویی، درایور ویدیو را در صفحه تنظیمات عوض کنید. پس از آن لازم است آنکی دوباره راه‌اندازی شود.

### تغییر درایور از Terminal.app {#changing-the-driver-from-terminalapp}
نسخه‌های قدیمی‌تر آنکی گزینه‌ای در تنظیمات نداشتند، اما اجازه می‌دادند درایور را با باز کردن Terminal.app و چسباندن موارد زیر و زدن <kbd>Enter</kbd> تنظیم کنید:

```
echo software > ~/Library/Application\\ Support/Anki2/gldriver6
```

چیزی چاپ نمی‌کند. سپس می‌توانید آنکی را دوباره شروع کنید.

اگر می‌خواهید به پیش‌فرض برگردید، `software` را به `auto` تغییر دهید، یا آن پرونده را حذف کنید.

## eGPUها {#egpus}

اگر هنگام استفاده از کارت گرافیک خارجی روی مک صفحه‌های خالی می‌بینید، می‌توانید روی برنامه آنکی <kbd>Ctrl</kbd>-کلیک کنید، روی **Get Info** کلیک کنید و گزینه **prefer eGPU** را فعال کنید.

## مانیتورها با رزولوشن‌های متفاوت {#monitors-with-different-resolutions}

[این پست انجمن](https://forums.ankiweb.net/t/mac-known-issues-wording-suggestion/7331) را ببینید.
