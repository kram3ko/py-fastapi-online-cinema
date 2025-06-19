from abc import ABC, abstractmethod
from typing import Union


class StorageInterface(ABC):
    """Base interface for all storage implementations"""
    @abstractmethod
    async def upload_file(self, file_name: str, file_data: Union[bytes, bytearray]) -> None:
        """
        Uploads a file to the storage.

        :param file_name: The name of the file to be stored.
        :param file_data: The file data in bytes.
        """
        pass

    @abstractmethod
    async def get_file_url(self, file_name: str) -> str:
        """
        Generate a public URL for a file stored in the storage.

        :param file_name: The name of the file stored.
        :return: The full URL to access the file.
        """
        pass


class S3StorageInterface(StorageInterface):
    """Interface for S3-compatible storage implementations"""
    @abstractmethod
    async def upload_file(self, file_name: str, file_data: Union[bytes, bytearray]) -> None:
        pass

    @abstractmethod
    async def get_file_url(self, file_name: str) -> str:
        pass


class DropboxStorageInterface(StorageInterface):
    """Interface for Dropbox storage implementations"""
    @abstractmethod
    async def upload_file(self, file_name: str, file_data: Union[bytes, bytearray]) -> None:
        pass

    @abstractmethod
    async def get_file_url(self, file_name: str) -> str:
        pass
