import mysql.connector, boto3
from mysql.connector.errors import InterfaceError, ProgrammingError, NotSupportedError

from config import DATABASES, S3_CONFIG

# make s3 connection
def get_s3_connection():
    s3_connection = boto3.client(
        's3',
        aws_access_key_id = S3_CONFIG['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key = S3_CONFIG['AWS_SECRET_ACCESS_KEY'],
        region_name = S3_CONFIG['REGION_NAME'],
    )
    return s3_connection


# make mysql database connection
class DatabaseConnection:

    def __init__(self):

        """ database connection 생성

        Returns:
            database connection 객체

        Authors:
            yoonhc@brandi.co.kr (윤희철)
            leesh3@brandi.co.kr (이소헌)

        History:
            2020-03-30 (yoonhc@brandi.co.kr): 초기 생성
            2020-04-01 (leesh3@brandi.co.kr): 클래스화
        """
        self.db_config = {
            'database': DATABASES['database'],
            'user': DATABASES['user'],
            'password': DATABASES['password'],
            'host': DATABASES['host'],
            'port': DATABASES['port'],
            'charset': DATABASES['charset'],
            'collation': DATABASES['collation'],
        }
        try:
            self.db_connection = mysql.connector.connect(**self.db_config)

        except InterfaceError as e:
            print(f'INTERFACE_ERROR_WITH {e}')
            return

        except ProgrammingError as e:
            print(f'PROGRAMMING_ERROR_WITH {e}')
            return

        except NotSupportedError as e:
            print(f'NOT_SUPPORTED_ERROR_WITH {e}')

    def __enter__(self) -> 'cursor':
        self.cursor = self.db_connection.cursor(buffered=True, dictionary=True)
        return self.cursor

    def __exit__(self, exc_type, exc_value, exc_trance) -> None:
        self.cursor.close()

    def close(self):
        return self.db_connection.close()
