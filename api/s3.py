import aioboto3

ENDPOINT_URL = 'http://0.0.0.0:9000'
ACCESS_KEY = 'abc123'
SECRET_KEY = 'someSecretKey'
BUCKET_NAME = 'test-bucket'
VERSION = 's3v4'


class S3Client:
    def __init__(self, endpoint_url=ENDPOINT_URL, access_key=ACCESS_KEY, secret_key=SECRET_KEY, bucket_name=BUCKET_NAME, version='s3v4'):
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.version = version
        self.session = aioboto3.Session(region_name='public-read')
        self.client = None

    async def create_bucket(self, bucket_name, region=None):
        """Создает бакет в S3 с указанным именем и регионом"""
        async with self.session.client("s3", endpoint_url=ENDPOINT_URL, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name='public-read') as s3:
            await s3.create_bucket(Bucket=bucket_name)
            print(f'Бакет {bucket_name} успешно создан.')

    async def upload_file(self, file, filename: str):
        async with self.session.client("s3", endpoint_url=ENDPOINT_URL, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name='public-read') as s3:
            await s3.upload_fileobj(file, self.bucket_name, filename)

    async def download_file(self, filename: str):
        s3_file: dict = {}
        async with self.session.resource("s3", endpoint_url=ENDPOINT_URL, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name='public-read') as s3:
            bucket = await s3.Bucket(BUCKET_NAME)
            obj = await s3.Object(self.bucket_name, key=filename)
            s3_file = await obj.get()
            data = await s3_file['Body'].read()
            return data

            # async with aiofiles.open('local_filename', 'wb') as file:
            #     await file.write(data)


# s3 = S3Client()
