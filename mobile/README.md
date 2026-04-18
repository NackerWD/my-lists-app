# Generar APK Android (TWA — Trusted Web Activity)

## Prerequisites

- Node.js 18+
- Java JDK 17+
- Android SDK (amb `ANDROID_HOME` configurat)

## Instal·lació Bubblewrap

```bash
npm install -g @bubblewrap/cli
```

## Primer ús — inicialitzar el projecte

Executa des de la carpeta `mobile/`:

```bash
cd mobile
bubblewrap init --manifest=https://staging.tuapp.vercel.app/manifest.json
```

Bubblewrap llegirà el `manifest.json` de la URL de staging i crearà el projecte
Android. Generarà un keystore (`android.keystore`) per signar l'APK.

> **Important:** guarda el keystore i la seva contrasenya en un lloc segur.
> Sense el keystore original no pots publicar actualitzacions a la mateixa app.

## Generar APK

```bash
bubblewrap build
```

L'APK signat es genera a `mobile/app-release-signed.apk`.

## Instal·lar en un dispositiu Android

```bash
adb install app-release-signed.apk
```

O copia l'APK manualment al dispositiu i instal·la'l des del gestor de fitxers.

## Actualitzar assetlinks.json amb el fingerprint real

Quan Bubblewrap genera el keystore, cal obtenir el SHA-256 fingerprint i
actualitzar `web/public/.well-known/assetlinks.json`:

```bash
keytool -list -v -keystore android.keystore -alias android
```

Copia el valor `SHA256:` (format `AA:BB:CC:...`) i substitueix el placeholder
a `web/public/.well-known/assetlinks.json`:

```json
{
  "sha256_cert_fingerprints": ["AA:BB:CC:DD:..."]
}
```

Fes deploy del frontend perquè Chrome pugui verificar l'app.

## Actualitzar l'app (noves versions)

1. Incrementa `appVersionCode` i `appVersionName` a `twa-manifest.json`
2. Executa `bubblewrap build` de nou
3. Distribueix el nou APK

## Notes

- El `twa-manifest.json` d'aquesta carpeta és la configuració de referència.
  Bubblewrap pot generar el seu propi `twa-manifest.json` durant `bubblewrap init`.
- El `fallbackType: "customtabs"` significa que si Chrome no té suport TWA,
  obrirà la URL com a Custom Tab en lloc de mostrar una pantalla d'error.
- `package_name` i `host` a `assetlinks.json` han de coincidir exactament
  amb els valors del `twa-manifest.json`.
