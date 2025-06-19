from typing import Union

import dropbox
from dropbox.exceptions import ApiError, AuthError

from storages.interfaces import DropboxStorageInterface


class DropboxStorageClient(DropboxStorageInterface):
    def __init__(
        self,
        access_token: str | None,
        app_key: str | None = None,
        app_secret: str | None = None,
        refresh_token: str | None = None
    ):
        """
        Initialize the Dropbox Storage Client.

        Args:
            access_token (str): Dropbox OAuth2 access token
            app_key (str, optional): Dropbox app key
            app_secret (str, optional): Dropbox app secret
            refresh_token (str, optional): Dropbox OAuth2 refresh token
        """
        if not access_token:
            raise ValueError("Dropbox access token must be provided")
        if not app_key or not app_secret:
            raise ValueError("Dropbox app key and secret must be provided")

        self._access_token = access_token
        self._app_key = app_key
        self._app_secret = app_secret
        self._refresh_token = refresh_token

        # Initialize Dropbox client with refresh token if available
        if refresh_token:
            self._dbx = dropbox.Dropbox(
                oauth2_refresh_token=refresh_token,
                app_key=app_key,
                app_secret=app_secret
            )
        else:
            self._dbx = dropbox.Dropbox(
                oauth2_access_token=access_token,
                app_key=app_key,
                app_secret=app_secret
            )

    async def upload_file(self, file_name: str, file_data: Union[bytes, bytearray]) -> None:
        """
        Upload a file to Dropbox storage.

        Args:
            file_name (str): The name of the file to be stored.
            file_data (Union[bytes, bytearray]): The file data in bytes.

        Raises:
            DropboxConnectionError: If there is a connection error with Dropbox.
            DropboxFileUploadError: If the file upload fails.
        """
        try:
            # Upload to Dropbox
            self._dbx.files_upload(
                file_data,
                f"/online-cinema/{file_name}",
                mode=dropbox.files.WriteMode.overwrite
            )
        except (AuthError, ApiError) as e:
            raise ConnectionError(f"Failed to connect to Dropbox storage: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to upload to Dropbox storage: {str(e)}") from e

    async def get_file_url(self, file_name: str) -> str:
        """
        Generate a temporary URL for a file stored in Dropbox.

        Args:
            file_name (str): The name of the file stored in Dropbox.

        Returns:
            str: The temporary URL to access the file.
        """
        try:
            # Create a temporary link that expires in 4 hours
            link = self._dbx.files_get_temporary_link(f"/online-cinema/{file_name}")
            return link.link
        except Exception as e:
            raise RuntimeError(f"Failed to get file URL from Dropbox: {str(e)}") from e
