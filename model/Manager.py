from os import path
from pathlib import Path

from model import rsa2048
from model.pyaes import AESModeOfOperationCTR, Encrypter, Decrypter, PADDING_DEFAULT
from model.pyaes.blockfeeder import _feed_stream, BLOCK_SIZE


class Manager:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.encrypt_types = {
            'encode_rsa': self._encode_rsa,
            'encode_rsa_stream': self._encode_rsa_stream,
            'encode_aes': self._encode_aes,
            'encode_aes_stream': self._encode_aes_stream,
            'decode_rsa': self._decode_rsa,
            'decode_rsa_stream': self._decode_rsa_stream,
            'decode_aes': self._decode_aes,
            'decode_aes_stream': self._decode_aes_stream
        }

    def _encode_rsa(self, name, key):
        filename = rsa2048.encode_file(key, path.join(self.upload_folder, name))
        return Path(filename).name

    def _encode_rsa_stream(self, name, key):
        return rsa2048.encode_file_yield(key, path.join(self.upload_folder, name))

    def _encode_aes(self, name, key):
        filename = path.join(self.upload_folder, name)
        data = open(filename, mode="rb").read()
        mode = AESModeOfOperationCTR(key)
        encrypted_data = mode.encrypt(data)
        filename = Path(filename)
        encoded_filename = filename.with_stem(f'encoded_{filename.stem}')
        with open(encoded_filename, 'wb+') as encoded_file:
            encoded_file.write(encrypted_data)
        return encoded_filename.name

    def _encode_aes_stream(self, name, key):
        filename = path.join(self.upload_folder, name)
        mode = AESModeOfOperationCTR(key)
        encrypter = Encrypter(mode, padding=PADDING_DEFAULT)
        return _feed_stream(encrypter, open(filename, mode="rb"), BLOCK_SIZE)

    def _decode_rsa(self, name, key):
        filename = rsa2048.decode_file(key, path.join(self.upload_folder, name))
        return Path(filename).name

    def _decode_rsa_stream(self, name, key):
        return rsa2048.decode_file_yield(key, path.join(self.upload_folder, name))

    def _decode_aes(self, name, key):
        filename = path.join(self.upload_folder, name)
        data = open(filename, mode="rb").read()
        mode = AESModeOfOperationCTR(bytes(key))
        decrypted_data = mode.decrypt(data)
        filename = Path(filename)
        decoded_filename = filename.with_stem(f'decoded_{filename.stem}')
        with open(decoded_filename, 'wb+') as decoded_file:
            decoded_file.write(decrypted_data)
        return decoded_filename.name

    def _decode_aes_stream(self, name, key):
        filename = path.join(self.upload_folder, name)
        mode = AESModeOfOperationCTR(key)
        decrypter = Decrypter(mode, padding=PADDING_DEFAULT)
        return _feed_stream(decrypter, open(filename, mode="rb"), BLOCK_SIZE)
