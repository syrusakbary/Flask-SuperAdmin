import cloudinary

from .base import CDNSession


class CloudinarySession(CDNSession):
    cdn = cloudinary

    def config(self, cloud_name, api_key, api_secret):
        self.cdn.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )

    def upload(self, img):
        self.cdn.uploader.upload(img)
