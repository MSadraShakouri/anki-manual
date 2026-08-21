# آنکی پوسته GTK را در گنوم/لینوکس برنمی‌دارد {#anki-not-picking-up-gtk-theme-on-gnomelinux}

می‌توانید با گفتن صریح پوسته GTK به آنکی، دور این مشکل بزنید. دستورهای زیر را در ترمینال اجرا کنید:

```shell
theme=$(gsettings get org.gnome.desktop.interface gtk-theme)
echo "gtk-theme-name=$theme" >> ~/.gtkrc-2.0
echo "export GTK2_RC_FILES=$HOME/.gtkrc-2.0" >> ~/.profile
```

سپس از رایانه‌تان خارج و دوباره وارد شوید تا آنکی پوسته GTK را بردارد.
