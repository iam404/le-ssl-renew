import os
import sys
import subprocess
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders


def EESendMail(send_from, send_to, subject, text, files, server="localhost",
               port=587, username='', password='', isTls=True):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f, "rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{0}"'
                        .format(os.path.basename(f)))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if isTls:
        smtp.starttls()

    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()


class CommandExecutionError(Exception):
    """custom Exception for command execution"""
    pass

class EEShellExec():
    """Method to run shell commands"""
    def __init__(self):
        pass

    def cmd_exec(command, errormsg='', log=True):
        """Run shell command from Python"""
        try:
            print("Running command: {0}".format(command))

            with subprocess.Popen([command], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, shell=True) as proc:
                (cmd_stdout_bytes, cmd_stderr_bytes) = proc.communicate()
                (cmd_stdout, cmd_stderr) = (cmd_stdout_bytes.decode('utf-8',
                                            "replace"),
                                            cmd_stderr_bytes.decode('utf-8',
                                            "replace"))

            if proc.returncode == 0:
                print("Command Output: {0}, \nCommand Error: {1}"
                                .format(cmd_stdout, cmd_stderr))
                return True
            else:
                print("Command Output: {0}, \nCommand Error: {1}"
                                .format(cmd_stdout, cmd_stderr))
                return False
        except OSError as e:
                raise CommandExecutionError
        except Exception as e:
                raise CommandExecutionError


    def cmd_exec_stdout(command, errormsg='', log=True):
        """Run shell command from Python"""
        try:
            print("Running command: {0}".format(command))
            with subprocess.Popen([command], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, shell=True) as proc:
                (cmd_stdout_bytes, cmd_stderr_bytes) = proc.communicate()
                (cmd_stdout, cmd_stderr) = (cmd_stdout_bytes.decode('utf-8',
                                            "replace"),
                                            cmd_stderr_bytes.decode('utf-8',
                                            "replace"))
            if proc.returncode == 0:
                return cmd_stdout
            else:
                return cmd_stdout
        except OSError as e:
                raise CommandExecutionError
        except Exception as e:
                raise CommandExecutionError


class SSL:
   def getExpirationDays(domain,returnonerror=False):
        # check if exist
        if not os.path.isfile('/etc/letsencrypt/live/{0}/cert.pem'
                      .format(domain)):
             if returnonerror:
                return -1
        current_date = EEShellExec.cmd_exec_stdout( "date -d \"now\" +%s")
        expiration_date =  EEShellExec.cmd_exec_stdout("date -d \"`openssl x509 -in /etc/letsencrypt/live/{0}/cert.pem"
                                           " -text -noout|grep \"Not After\"|cut -c 25-`\" +%s".format(domain))

        days_left = int((int(expiration_date) - int(current_date))/ 86400)
        if (days_left > 0):
            return days_left
        else:
            # return "Certificate Already Expired ! Please Renew soon."
            print("Not renewing")
            sys.exit()

   def getExpirationDate(domain):
        # check if exist
        if not os.path.isfile('/etc/letsencrypt/live/{0}/cert.pem'
                      .format(domain)):
            print('File Not Found : /etc/letsencrypt/live/{0}/cert.pem'
                      .format(domain),False)

        expiration_date =  EEShellExec.cmd_exec_stdout("date -d \"`openssl x509 -in /etc/letsencrypt/live/{0}/cert.pem"
                                           " -text -noout|grep \"Not After\"|cut -c 25-`\" ".format(domain))
        return expiration_date

def cloneLetsEncrypt():
    letsencrypt_repo = "https://github.com/letsencrypt/letsencrypt"
    if not os.path.isdir("/opt"):
        os.makedirs("/opt")
    try:
        print("Downloading {0:20}".format("LetsEncrypt"))
        os.chdir('/opt/')
        EEShellExec.cmd_exec("git clone {0}".format(letsencrypt_repo))
        return True
    except Exception as e:
        print("Unable to download file, LetsEncrypt")
        return False


def renewLetsEncrypt(ee_domain_name):
   # ee_wp_email = "prasad.nevase@rtcamp.com"
    ee_wp_email = "prabuddha.chakraborty@rtcamp.com"

    if not os.path.isdir("/opt/letsencrypt"):
        cloneLetsEncrypt()
    os.chdir('/opt/letsencrypt')
    EEShellExec.cmd_exec("git pull")

    print("Renewing SSl cert for https://{0}".format(ee_domain_name))

    ssl = EEShellExec.cmd_exec("./letsencrypt-auto --renew certonly --webroot -w /var/www/{0}/htdocs/ -d {0} "
                                .format(ee_domain_name)
                                + "--email {0} --text --agree-tos".format(ee_wp_email))
    mail_list = ''
    if not ssl:
        print("ERROR : Cannot RENEW SSL cert !",False)
        if (SSL.getExpirationDays(ee_domain_name)>0):
                    print("Your current cert will expire within " + str(SSL.getExpirationDays(ee_domain_name)) + " days.",False)
        else:
                    print("Your current cert already EXPIRED !",False)

        EESendMail("renew@{0}".format(ee_domain_name), ee_wp_email, "[FAIL] SSL cert renewal {0}".format(ee_domain_name),
                       "Hey Hi,\n\nSSL Certificate renewal for https://{0} was unsuccessful.".format(ee_domain_name) +
                       "\nPlease check easyengine log for reason. Your SSL Expiry date : " +
                            str(SSL.getExpirationDate(ee_domain_name)) +
                       "\n\nFor support visit https://easyengine.io/support/ .\n\nYour's faithfully,\n",files=mail_list,
                        port=25, isTls=False)

    EESendMail("renew@{0}".format(ee_domain_name), ee_wp_email, "[SUCCESS] SSL cert renewal {0}".format(ee_domain_name),
                       "Hey Hi,\n\nYour SSL Certificate has been renewed for https://{0} .".format(ee_domain_name) +
                       "\nYour SSL will Expire on : " +
                            str(SSL.getExpirationDate(ee_domain_name)) +
                       "\n\nYour's faithfully,\n",files=mail_list,
                        port=25, isTls=False)


if __name__ == '__main__':
    print( "\n\nStarted ..SSL renew script For Lets Encrypt")
    print(EEShellExec.cmd_exec_stdout( "date -d \"now\""))
    domain= sys.argv[1]
    expiry_days = SSL.getExpirationDays(domain)
    print(expiry_days)
    min_expiry_days = 30
    if (expiry_days <= min_expiry_days):
        renewLetsEncrypt(domain)
