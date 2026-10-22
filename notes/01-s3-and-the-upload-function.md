# 01 — S3 basics, and writing `upload_image`

## What S3 actually is

Not a filesystem, not a database — object storage. Three ideas matter for this project:

- **Bucket** — a top-level container with a globally unique name across all of AWS, not just my account. I'm using the existing `nikblog-images` bucket.
- **Key** — the name/path of an object inside the bucket (e.g. `a1b2c3.png`). It looks like a filesystem path if it has slashes in it, but S3 doesn't actually have real folders — a key is just a string.
- **Public read, private write** — the same split already set up for Nik-Blog: anyone can `GetObject` (so images render on the public site), but only a credentialed IAM identity can `PutObject`/`DeleteObject`. That split is enforced by two separate things working together: the bucket policy (public read) and IAM (who can write).

The only S3 operation this project needs is `PutObject` — "store these bytes under this key in this bucket."

## `boto3`, in two steps

1. **A client** — a handle representing the connection to S3, not an upload by itself:
   ```python
   s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])
   ```
   `boto3` reads `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` from the environment automatically — nothing to pass by hand, as long as they're set under those exact names.

2. **The actual call**:
   ```python
   s3.put_object(
       Bucket=os.environ["S3_BUCKET_NAME"],
       Key=key,
       Body=file_bytes,
       ContentType="image/png",
   )
   ```
   `Body` has to be the raw bytes of the file, not its path — reading the file into memory is a separate step that happens first.

## Why a random key, not the original filename

Same two reasons as Nik-Blog's own `s3Service.js`:
- **Collision avoidance** — two uploads both named `cover.png` would silently overwrite each other.
- **Not leaking my local filesystem** — a downloaded file's original name (e.g. `gemini-output-final-v2.png`) has no reason to end up in a public URL.

`secrets.token_hex(16)` instead of the `random` module, specifically because `secrets` is built for exactly this (unpredictable values), where `random` is not.

## `upload_image`, built step by step

```python
def upload_image(local_path: Path) -> str:
    extension = local_path.suffix
    random_name = secrets.token_hex(16)
    key = f"{random_name}{extension}"
    file_bytes = local_path.read_bytes()

    s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])
    s3.put_object(
        Bucket=os.environ["S3_BUCKET_NAME"],
        Key=key,
        Body=file_bytes,
        ContentType="image/png",
    )

    bucket = os.environ["S3_BUCKET_NAME"]
    region = os.environ["AWS_REGION"]
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
```

`Path.read_bytes()` does the "open, read, close" in one call — no manual file handle to manage. The function's only job is upload-and-return-a-URL; it doesn't know or care what that URL is going to be used for afterward (that's `nikblog_client.py`'s job, next).

## Real mistakes caught while writing this (not glossed over)

- Called `.putObject(` (camelCase) instead of `.put_object(` — a JavaScript habit from reading Nik-Blog's own `s3Service.js` right before writing this.
- Chained `boto3.client(...).put_object(...)` directly into the `s3` variable, which would have made `s3` hold the API response instead of the reusable client — split into two statements.
- Missing comma between keyword arguments — not a logic bug, just Python syntax (every `name=value` pair in a call needs one after it except the last).

## A real limitation found later, not at build time

The first version hardcoded `ContentType="image/png"` on every upload — it worked for the one test image, but Nik-Blog's own upload form also accepts short video clips (`video/mp4`, `video/webm`, per `backend/middleware/uploadImage.js`'s allowed types). Nikan asked whether this server could handle video too, which is what actually surfaced it: technically yes, since the function just reads and uploads raw bytes regardless of type — but every upload would land on S3 tagged `image/png`, including an actual `.mp4` file.

The frontend itself doesn't care — `isVideoUrl.ts` decides image-vs-video from the URL's file extension, not the S3 object's `Content-Type` header — but a video served with the wrong `Content-Type` can still fail to play correctly in a browser, since that header is what tells the browser how to actually handle the response.

Fixed with Python's built-in `mimetypes` module instead of a hardcoded value:

```python
content_type, _ = mimetypes.guess_type(local_path.name)
if content_type is None:
    content_type = "application/octet-stream"
```

Verified for real, not just by reading the code: uploaded a real file and then called `s3.head_object()` to read back the object's actual stored `Content-Type` from S3 — confirmed it matches the file's real type, not a guess from what the function returns.
