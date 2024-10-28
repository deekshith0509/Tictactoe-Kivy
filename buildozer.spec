[app]
title = TicTacToe
package.name = tictactoe
package.domain = org.deekshith

android.archs = arm64-v8a
source.main = main.py
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,dm
orientation = portrait
requirements = python3,kivy,kivymd,markdown,materialyoucolor,exceptiongroup,asyncgui,asynckivy
fullscreen = 0
version = 0.2
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO

android.release_artifact = apk
android.presplash_color = #FFFFFF

debug = 1
android.allow_backup = True
android.logcat = True
android.ndk = 25b
android.api = 33
log_level = 2