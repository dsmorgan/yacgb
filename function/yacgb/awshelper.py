import boto3
import os
from base64 import b64decode
import logging

logger = logging.getLogger(__name__)

def decrypt_environ(enc_environ):
    e = os.environ[enc_environ]
    # Decrypt code should run once and variables stored outside of the function
    # handler so that these are decrypted once per container
    de = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(e),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']})['Plaintext'].decode('utf-8')
    logger.info("Decrypted via KMS: " + enc_environ)
    return(de)