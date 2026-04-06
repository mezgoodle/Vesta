# Vesta Mobile App (Flutter, Android)

Мобільний клієнт для Vesta backend з auth, chat, voice loop та Home Control.

## 1) Передумови

- Flutter SDK 3.22+ (stable)
- Android SDK + Android Studio (або встановлені Android command-line tools)
- Працюючий backend Vesta

## 2) Налаштування

```bash
cd mobile_app
flutter pub get
```

## 3) Конфіг API Base URL

Додаток читає API URL з `--dart-define`:

- `API_BASE_URL` (дефолт: `http://10.0.2.2:8000`)

Приклад запуску на Android emulator:

```bash
flutter run \
  --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

> Для фізичного Android-девайса використовуйте IP машини у локальній мережі, наприклад `http://192.168.1.50:8000`.

## 4) Що реалізовано

- **Auth** через `POST /api/v1/login/access-token` (x-www-form-urlencoded)
- **Secure token storage** через `flutter_secure_storage`
- **Chat** через `POST /api/v1/chat/process` з `want_voice=true`
- **Voice loop**:
  - STT через `speech_to_text`
  - запит в `/chat/process`
  - відтворення `voice_audio` (base64)
  - fallback на `POST /api/v1/tts/synthesize`
- **Home Control**:
  - читання девайсів (`GET /api/v1/devices`)
  - CRUD керування девайсами (`/api/v1/devices/*`)

## 5) Запуск

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

## 6) Debug APK build

```bash
flutter build apk --debug \
  --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

APK після білду:

- `build/app/outputs/flutter-apk/app-debug.apk`

## 7) Доступи Android (мікрофон)

У `android/app/src/main/AndroidManifest.xml` додано:

- `android.permission.RECORD_AUDIO`
- `android.permission.INTERNET`

