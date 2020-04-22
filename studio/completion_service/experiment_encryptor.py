from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
import nacl.secret
import nacl.utils
import base64

from studio.workload_modifier import WorkloadModifier
from studio import logs

class ExperimentEncryptor(WorkloadModifier):
    """
    Implementation for experiment workload encryption.
    """
    def __init__(self, name: str, keypath: str):
        super(ExperimentEncryptor, self).__init__(name)

        # XXX Set logger verbosity level here
        self.logger = logs.getLogger(self.__class__.__name__)

        self.key_path = keypath
        self.recipient_key = None
        try:
            self.recipient_key = RSA.import_key(open(self.key_path).read())
        except:
            self.logger.error(
                "FAILED to import recipient public key from: {0}".format(self.key_path))
            return


    def modify(self, workload):
        pass

    def _import_rsa_key(self, key_path: str):
        key = None
        try:
            key = RSA.import_key(open(key_path).read())
        except:
            self.logger.error(
                "FAILED to import RSA key from: {0}".format(key_path))
            key = None
        return key

    def _encrypt_str(self, workload: str):
        # Generate one-time symmetric session key:
        session_key = nacl.utils.random(32)

        # Encrypt the data with the NaCL session key
        data_to_encrypt = workload.encode("utf-8")
        box_out = nacl.secret.SecretBox(session_key)
        encrypted_data = box_out.encrypt(data_to_encrypt)
        encrypted_data_text = base64.b64encode(encrypted_data)

        # Encrypt the session key with the public RSA key
        cipher_rsa = PKCS1_OAEP.new(self.recipient_key)
        encrypted_session_key = cipher_rsa.encrypt(session_key)
        encrypted_session_key_text = base64.b64encode(encrypted_session_key)

        return encrypted_session_key_text, encrypted_data_text

    def _decrypt_data(self, private_key_path, encrypted_key_text, encrypted_data_text):
        private_key = self._import_rsa_key(private_key_path)
        if private_key is None:
            return None

        try:
            private_key = RSA.import_key(open(private_key_path).read())
        except:
            self.logger.error(
                "FAILED to import private key from: {0}".format(private_key_path))
            return None

        # Decrypt the session key with the private RSA key
        cipher_rsa = PKCS1_OAEP.new(private_key)
        session_key = cipher_rsa.decrypt(
            base64.b64decode(encrypted_key_text))

        # Decrypt the data with the NaCL session key
        box_in = nacl.secret.SecretBox(session_key)
        decrypted_data = box_in.decrypt(
            base64.b64decode(encrypted_data_text))
        decrypted_data = decrypted_data.decode("utf-8")

        return decrypted_data

def main():
    print("Hello!")
    encryptor = ExperimentEncryptor("StudioExperimentEncryptor", "keys/receiver.pem")

    enc_key, enc_data = encryptor._encrypt_str("Есть только миг Hello Hello Mr Monkey!")
    print("Encrypted: key: {0} \ndata: {1}".format(enc_key, enc_data))


    decrypt_data = encryptor._decrypt_data("keys/private.pem", enc_key, enc_data)

    print("Return: {0}".format(decrypt_data))



    pass

if __name__ == '__main__':
    main()

