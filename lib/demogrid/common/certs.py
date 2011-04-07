'''
Created on Apr 6, 2011

@author: borja
'''
from OpenSSL import crypto, SSL

class CertificateGenerator(object):
    def __init__(self, ca_cert = None, ca_key = None):
        self.ca_cert = ca_cert
        self.ca_key = ca_key
        self.serial = 1
        
    def set_ca(self, ca_cert, ca_key):
        self.ca_cert = ca_cert
        self.ca_key = ca_key
        
    def gen_selfsigned_ca_cert(self, cn):
        return self.__gen_certificate(cn = cn, 
                                      issuer_cert = None,
                                      issuer_key = None)

    def gen_user_cert(self, cn):
        return self.__gen_certificate(cn = cn, 
                                      issuer_cert = self.ca_cert,
                                      issuer_key = self.ca_key)

    def gen_host_cert(self, hostname):
        return self.__gen_certificate(cn = "host/"+hostname, 
                                      issuer_cert = self.ca_cert,
                                      issuer_key = self.ca_key)
        
    def __gen_certificate(self, cn, issuer_cert, issuer_key):
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)

        cert = crypto.X509()
        cert.get_subject().O = "Grid"
        cert.get_subject().OU = "DemoGrid"
        cert.get_subject().CN = cn
        cert.set_serial_number(self.serial)
        self.serial += 1
        cert.set_version(2)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*365*24*60*60)
        cert.set_pubkey(k)

        
        if issuer_cert == None:
            cert.set_issuer(cert.get_subject())
        else:
            cert.set_issuer(issuer_cert.get_subject())
            
        if issuer_cert == None:
            cert.sign(k, 'sha1')
        else:
            cert.sign(issuer_key, 'sha1')   
        
        return cert, k 
    
    def save_certificate(self, cert, key, cert_file, key_file):
        cert_file = open(cert_file, "w")
        cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        cert_file.close()  
    
        key_file = open(key_file, "w")
        key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
        key_file.close()        
        
    def load_certificate(self, cert_file, key_file):
        cert_file = open(cert_file, "r")
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_file.read())
        cert_file.close()  
    
        key_file = open(key_file, "r")
        key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_file.read())
        key_file.close()      
        
        return cert, key