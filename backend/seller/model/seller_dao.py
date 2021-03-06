import pandas as pd, uuid, os
from flask import jsonify
from mysql.connector.errors import Error

from connection import get_s3_connection


class SellerDao:
    """ 셀러 모델

    Authors:
        leesh3@brandi.co.kr (이소헌)
    History:
        2020-03-25 (leesh3@brandi.co.kr): 초기 생성

    """
    # noinspection PyMethodMayBeStatic
    def gen_random_name(self):

        """ 랜덤한 이름 생성

        Args:
            self: 클래스에서 전역으로 쓰임

        Returns: http 응답코드
            random_name: 랜덤한 이름

        Authors:
            yoonhc@brandi.co.kr (윤희철)

        History:
            2020-04-07 (yoonhc@brandi.co.kr): 초기 생성
        """
        random_name = str(uuid.uuid4())
        return random_name

    # noinspection PyMethodMayBeStatic
    def get_account_password(self, change_info, db_connection):

        """ 계정의 암호화된 비밀번호 표출

        비밀번호 변경 시 기존 비밀번호를 제대로 입력했는지 확인하기 위해,
        인자로 받아온 change_info['parameter_account_no'] 의 password 를 표출합니다.

        Args:
            change_info: account 정보
            (parameter_account_no: 비밀번호를 확인할 account_no)
            db_connection: 연결된 database connection 객체

        Returns:
            200: 요청된 계정의 계정번호 및 암호화된 비밀번호
            500: DB_CURSOR_ERROR, INVALID_KEY

        Authors:
            leejm3@brandi.co.kr (이종민)

        History:
            2020-03-31 (leejm3@brandi.co.kr): 초기 생성
            2020-04-12 (leejm3@brandi.co.kr):
                - 받는 인자 명칭을 명확히 하기 위해 변경(account_info -> change_info)
                - sql 바인딩용 데이터를 따로 만들었는데, 인자로 받은 change_info 를 그대로 사용하도록 변경
        """

        try:
            with db_connection.cursor() as db_cursor:

                # accounts 테이블 SELECT
                select_account_password_statement = """
                    SELECT account_no, password 
                    FROM accounts 
                    WHERE account_no = %(parameter_account_no)s
                """

                # SELECT 문 실행
                db_cursor.execute(select_account_password_statement, change_info)

                # 쿼리로 나온 기존 비밀번호를 가져옴
                original_password = db_cursor.fetchone()
                return original_password

        except KeyError as e:
            print(f'KEY_ERROR WITH {e}')
            return jsonify({'message': 'INVALID_KEY'}), 500

        except Error as e:
            print(f'DATABASE_CURSOR_ERROR_WITH {e}')
            return jsonify({'message': 'DB_CURSOR_ERROR'}), 500

    # noinspection PyMethodMayBeStatic
    def change_password(self, change_info, db_connection):

        """ UPDATE 계정 비밀번호 DB

        Args:
            change_info:
                parameter_account_no: 비밀번호가 바뀌어야할 계정 번호
                original_password: 기존 비밀번호
                new_password: 새로운 비밀번호

            db_connection: 연결된 database connection 객체

        Returns: http 응답코드
            200: SUCCESS 비밀번호 변경 완료
            400: INVALID_PARAMETER_ACCOUNT_NO
            500: DB_CURSOR_ERROR, INVALID_KEY

        Authors:
            leejm@brandi.co.kr (이종민)

        History:
            2020-03-31 (leejm3@brandi.co.kr): 초기 생성
            2020-04-12 (leejm3@brandi.co.kr):
                - 비밀번호 변경을 적용할 계정번호가 없으면 'INVALID_PARAMETER_ACCOUNT_NO' 반환하도록 수정
                - 받는 인자 명칭을 명확히 하기 위해 변경(account_info -> change_info)
                - sql 바인딩용 데이터를 따로 만들었는데, 인자로 받은 change_info 를 그대로 사용하도록 변경
                - 주석 수정(Args)
                    - change_info 인자 중 dao 에서 사용하는 인자에 대한 설명 추가
                    - INVALID_PARAMETER_ACCOUNT_NO 에러 추가
        """

        try:
            with db_connection.cursor() as db_cursor:

                # accounts 테이블 UPDATE
                update_password_statement = """
                    UPDATE 
                    accounts 
                    SET
                    password = %(password)s
                    WHERE
                    account_no = %(parameter_account_no)s
                """

                # UPDATE 문 실행
                db_cursor.execute(update_password_statement, change_info)

                # 비밀번호 변경을 적용할 계정번호가 없으면 에러 반환
                # 적용된 쿼리가 없으면 rowcount = 0 을 반환하는것을 이용
                if db_cursor.rowcount == 0:
                    return jsonify({'message': 'INVALID_PARAMETER_ACCOUNT_NO'}), 400

                # 실행 결과 반영
                db_connection.commit()

                return jsonify({'message': 'SUCCESS'}), 200

        except KeyError:
            return jsonify({'message': 'INVALID_KEY'}), 400

        except Error as e:
            print(f'DATABASE_CURSOR_ERROR_WITH {e}')
            return jsonify({'message': 'DB_CURSOR_ERROR'}), 500

    # noinspection PyMethodMayBeStatic
    def get_seller_info(self, account_info, db_connection):

        """ 계정의 셀러정보 표출

        인자로 받아온 account_info['parameter_account_no'] 의 셀러정보를 표출합니다.

        Args:
            account_info: account 정보
            (parameter_account_no: 셀러정보를 확인할 account_no)
            db_connection: 연결된 database connection 객체

        Returns:
            200: 요청된 계정의 셀러정보
            400: INVALID_ACCOUNT_NO
            500: DB_CURSOR_ERROR, INVALID_KEY

        Authors:
            leejm3@brandi.co.kr (이종민)

        History:
            2020-03-31 (leejm3@brandi.co.kr): 초기 생성
            2020-04-01 (leejm3@brandi.co.kr): seller_info 기본 정보 표출
            2020-04-02 (leejm3@brandi.co.kr): 외래키 관련 정보 표출
            2020-04-03 (leejm3@brandi.co.kr): 표출 정보에 외래키 id 값 추가
            2020-04-15 (leejm3@brandi.co.kr): 해당 계정이 없으면 에러 리턴 추가
            2020-04-16 (leejm3@brandi.co.kr): SQL 문 별칭 적용

        """
        try:
            with db_connection.cursor() as db_cursor:

                # 셀러 기본 정보(외래키 제외)
                # SELECT 문 조건 데이터
                account_info_data = {
                    'account_no': account_info['parameter_account_no']
                }

                # seller_info 테이블 SELECT (get 기본 정보)
                select_seller_info_statement = """
                    SELECT 
                        seller_info_no,
                        seller_account_id,
                        profile_image_url,
                        CS03.status_no as seller_status_no,
                        CS03.name as seller_status_name,
                        CS04.seller_type_no as seller_type_no,
                        CS04.name as seller_type_name,
                        CS05.account_no as account_no,
                        CS05.login_id as account_login_id,
                        CS06.app_user_no as brandi_app_user_no,
                        CS06.app_id as brandi_app_user_app_id,
                        name_kr,
                        name_en,
                        brandi_app_user_id,
                        ceo_name,
                        company_name,
                        business_number,
                        certificate_image_url,
                        online_business_number,
                        online_business_image_url,
                        background_image_url,
                        short_description,
                        long_description,
                        site_url,
                        insta_id,
                        center_number,
                        kakao_id,
                        yellow_id,
                        zip_code,
                        address,
                        detail_address,
                        weekday_start_time,
                        weekday_end_time,
                        weekend_start_time,
                        weekend_end_time,
                        bank_name,
                        bank_holder_name,
                        account_number
                    
                    FROM seller_accounts AS CS01
                    
                    -- seller_info 기본 정보
                    INNER JOIN seller_infos AS CS02
                    ON CS01.seller_account_no = CS02.seller_account_id
                    
                    -- 셀러 상태명
                    INNER JOIN seller_statuses as CS03
                    ON CS02.seller_status_id = CS03.status_no

                    -- 셀러 속성명
                    INNER JOIN seller_types as CS04
                    ON CS02.seller_type_id = CS04.seller_type_no

                    -- 셀러계정 로그인 아이디
                    LEFT JOIN accounts as CS05
                    ON CS05.account_no = CS01.account_id
                    AND CS05.is_deleted =0

                    -- 브랜디 앱 아이디
                    LEFT JOIN brandi_app_users as CS06
                    ON CS02.brandi_app_user_id = CS06.app_user_no
                    
                    WHERE 
                        -- 삭제되지 않은 계정의 최신 셀러정보 리스트, 삭제되지 않은 브랜디앱 아이디
                        CS01.account_id = %(account_no)s
                        AND CS01.is_deleted = 0
                        AND CS02.close_time = '2037-12-31 23:59:59'
                    
                """

                # SELECT 문 실행
                db_cursor.execute(select_seller_info_statement, account_info_data)

                # seller_info_result 에 쿼리 결과 저장
                seller_info_result = db_cursor.fetchone()

                # 해당 번호의 셀러가 없으면 에러 리턴
                if seller_info_result is None:
                    return seller_info_result

                # 담당자 정보
                # SELECT 문 조건 데이터
                seller_info_no_data = {
                    'seller_info_no': seller_info_result['seller_info_no']
                }
                # manager_infos 테이블 SELECT(get *)
                select_manager_infos_statement = """
                                SELECT
                                    MI02.name,
                                    MI02.contact_number,
                                    MI02.email,
                                    MI02.ranking
                                    
                                FROM 
                                    seller_infos AS MI01
                                
                                INNER JOIN 
                                    manager_infos AS MI02
                                    ON MI01.seller_info_no = MI02.seller_info_id
                                
                                WHERE 
                                    seller_info_no = %(seller_info_no)s
                                    AND MI02.is_deleted = 0
                                
                                LIMIT 3
                            """

                # SELECT 문 실행
                db_cursor.execute(select_manager_infos_statement, seller_info_no_data)

                # manager_infos 출력 결과 저장
                manager_infos = db_cursor.fetchall()

                # seller_info_result 에 manager_info 저장
                seller_info_result['manager_infos'] = [info for info in manager_infos]

                # 셀러 상태 변경 기록
                # SELECT 문 조건 데이터
                account_info_data = {
                    'seller_account_id': seller_info_result['seller_account_id']
                }

                # seller_status_change_histories 테이블 SELECT
                select_status_history_statement = """
                                SELECT
                                    changed_time,
                                    SH03.name as seller_status_name,
                                    SH04.login_id as modifier
                                
                                FROM
                                    seller_accounts as SH01

                                -- 셀러상태이력 기본정보
                                INNER JOIN
                                    seller_status_change_histories as SH02
                                    ON SH01.seller_account_no = SH02.seller_account_id

                                -- 셀러 상태명
                                INNER JOIN
                                    seller_statuses as SH03
                                    ON SH02.seller_status_id = SH03.status_no

                                -- 수정자 로그인아이디
                                LEFT JOIN
                                    accounts as SH04
                                    ON SH04.account_no = SH01.account_id

                                WHERE 
                                    SH01.seller_account_no = %(seller_account_id)s
                                    AND SH04.is_deleted = 0
                                
                                ORDER BY changed_time
                            """

                # SELECT 문 실행
                db_cursor.execute(select_status_history_statement, account_info_data)

                # seller_status_change_histories 출력 결과 저장
                status_histories = db_cursor.fetchall()

                # seller_info_result 에 seller_status_change_histories 저장
                seller_info_result['seller_status_change_histories'] = [history for history in status_histories]

                # 셀러 속성 리스트(마스터가 셀러의 속성 변경하는 옵션 제공용)
                # SELECT 문 조건 데이터
                account_info_data = {
                    'seller_info_no': seller_info_result['seller_info_no']
                }

                # seller_types 테이블 SELECT
                select_seller_types_statement = """
                                SELECT
                                    ST03.seller_type_no as seller_type_no,
                                    ST03.name as seller_type_name
                                
                                FROM 
                                product_sorts as ST01
                                
                                -- 셀러정보
                                INNER JOIN
                                    seller_infos as ST02
                                    ON ST01.product_sort_no = ST02.product_sort_id
                               
                                -- 상품속성
                                INNER JOIN
                                    seller_types as ST03
                                    ON ST01.product_sort_no = ST03.product_sort_id

                                WHERE 
                                ST02.seller_info_no = %(seller_info_no)s
                            """

                # SELECT 문 실행
                db_cursor.execute(select_seller_types_statement, account_info_data)

                # seller_types 출력 결과 저장
                seller_types = db_cursor.fetchall()

                # seller_info_result 에 seller_types 저장
                seller_info_result['seller_types'] = seller_types

                # seller_info_result 에 auth_type_id 저장

                seller_info_result['auth_type_id'] = account_info['auth_type_id']

                return seller_info_result

        except KeyError as e:
            print(f'KEY_ERROR WITH {e}')
            return jsonify({'message': 'INVALID_KEY'}), 500

        except Error as e:
            print(f'DATABASE_CURSOR_ERROR_WITH {e}')
            return jsonify({'message': 'DB_CURSOR_ERROR'}), 500

    # noinspection PyMethodMayBeStatic
    def get_seller_list(self, valid_param, db_connection):

        """ GET 셀러 리스트를 표출하고, 검색 키워드가 오면 키워드 별 검색 가능.
        페이지네이션 기능: offset 과 limit 값을 받아서 페이지네이션 구현.
        검색기능: 키워드를 받아서 검색기능 구현. 키워드가 추가 될 때 마다 검색어가 쿼리문에 추가됨
        엑셀다운로드 기능: excel=1을 쿼리파라미터로 받으면 데이터베이스의 값을
                        엑셀파일로 만들어 s3에 업로드하고 다운로드 링크를 리턴

        Args:
            db_connection: 연결된 database connection 객체
            valid_param: view 에서 validation 을 통과한 파라미터들을 가져옴.

        Returns: http 응답코드
            200: 키워드로 excel=1이 들어온 경우 s3에 올라간 엑셀파일 다운로드 url
            200: 셀러 리스트 표출(검색기능 포함), 키워드에 맞는 셀러 숫자
            500: SERVER ERROR

        Authors:
            yoonhc@brandi.co.kr (윤희철)

        History:
            2020-04-03(yoonhc@brandi.co.kr): 초기 생성
            2020-04-07(yoonhc@brandi.co.kr): 엑셀 다운로드 기능 추가
            2020-04-10(yoonhc@brandi.co.kr): 필터링 키워드가 들어오면 필터된 셀러를 count 하고 결과값에 추가하는 기능 작성
            2020-04-14(yoonhc@brandi.co.kr): 키워드가 들어오면 쿼리문 자체에 string 을 추가하고 db_connection 을 열고 바인딩하는 방식으로 변경.
        """

        # 키워드 검색을 위해서 쿼리문을 미리 정의해줌.
        select_seller_list_statement = '''
            SELECT 
            seller_account_id, 
            accounts.login_id,
            name_en,
            name_kr,
            brandi_app_user_id,
            seller_statuses.name as seller_status,
            seller_status_id,
            seller_types.name as seller_type_name,
            site_url,
            (
                SELECT COUNT(0) 
                FROM product_infos 
                WHERE product_infos.seller_id  = seller_infos.seller_account_id 
                AND product_infos.close_time = '2037-12-31 23:59:59' 
            ) as product_count,
            seller_accounts.created_at,
            manager_infos.name as manager_name,
            manager_infos.contact_number as manager_contact_number,
            manager_infos.email as manager_email,
            seller_infos.product_sort_id,
            profile_image_url,
            accounts.account_no
            FROM seller_infos
            right JOIN seller_accounts ON seller_accounts.seller_account_no = seller_infos.seller_account_id
            LEFT JOIN accounts ON seller_accounts.account_id = accounts.account_no
            LEFT JOIN seller_statuses ON seller_infos.seller_status_id = seller_statuses.status_no
            LEFT JOIN seller_types ON seller_infos.seller_type_id = seller_types.seller_type_no
            LEFT JOIN manager_infos on manager_infos.seller_info_id = seller_infos.seller_info_no 
            WHERE seller_infos.close_time = '2037-12-31 23:59:59.0'
            AND accounts.is_deleted = 0
            AND seller_accounts.is_deleted = 0
            AND manager_infos.ranking = 1
        '''

        # 키워드검색이 들어왔을 때 검색결과의 셀러를 count 하기위해서 count 용 쿼리도 미리 정의해줌.
        filter_query_values_count_statement = '''
            SELECT COUNT(0) as filtered_seller_count
            FROM seller_infos
            right JOIN seller_accounts ON seller_accounts.seller_account_no = seller_infos.seller_account_id
            LEFT JOIN accounts ON seller_accounts.account_id = accounts.account_no
            LEFT JOIN seller_statuses ON seller_infos.seller_status_id = seller_statuses.status_no
            LEFT JOIN seller_types ON seller_infos.seller_type_id = seller_types.seller_type_no
            LEFT JOIN manager_infos on manager_infos.seller_info_id = seller_infos.seller_info_no 
            WHERE seller_infos.close_time = '2037-12-31 23:59:59.0'
            AND accounts.is_deleted = 0
            AND seller_accounts.is_deleted = 0 
            AND manager_infos.ranking = 1
        '''

        # 쿼리파라미터에 키워드가 들어왔는지 확인하고 위에서 정의해준 명령문에 쿼리를 추가해줌.
        if valid_param.get('seller_account_no', None):
            select_seller_list_statement += " AND seller_accounts.seller_account_no = %(seller_account_no)s"
            filter_query_values_count_statement += " AND seller_accounts.seller_account_no = %(seller_account_no)s"

        if valid_param.get('login_id', None):
            select_seller_list_statement += " AND accounts.login_id = %(login_id)s"
            filter_query_values_count_statement += " AND accounts.login_id = %(login_id)s"

        # 셀러 한글명 같은 경우는 키워드로 들어온 값을 포함하는 모든 셀러를 검색해야 하기 때문에 like 문을 사용한다.
        name_kr = valid_param.get('name_kr', None)
        if valid_param.get('name_kr', None):
            valid_param['name_kr'] = '%'+name_kr+'%'
            select_seller_list_statement += " AND name_kr LIKE %(name_kr)s"
            filter_query_values_count_statement += " AND name_kr LIKE %(name_kr)s"

        if valid_param.get('name_en', None):
            select_seller_list_statement += " AND name_en = %(name_en)s"
            filter_query_values_count_statement += " AND name_en = %(name_en)s"

        if valid_param.get('brandi_app_user_id', None):
            select_seller_list_statement += " AND brandi_app_user_id = %(brandi_app_user_id)s"
            filter_query_values_count_statement += " AND brandi_app_user_id = %(brandi_app_user_id)s"

        if valid_param.get('manager_name', None):
            select_seller_list_statement += " AND manager_infos.name = %(manager_name)s"
            filter_query_values_count_statement += " AND manager_infos.name = %(manager_name)s"

        if valid_param.get('seller_status', None):
            select_seller_list_statement += " AND seller_statuses.name = %(seller_status)s"
            filter_query_values_count_statement += " AND seller_statuses.name = %(seller_status)s"

        # 담당자 연락처 같은 경우는 키워드로 들어온 값을 포함하는 모든 셀러를 검색해야 하기 때문에 like 문을 사용한다
        manager_contact_number = valid_param.get('manager_contact_number', None)
        if valid_param.get('manager_contact_number', None):
            valid_param['manager_contact_number'] = '%'+manager_contact_number+'%'
            select_seller_list_statement += " AND manager_infos.contact_number LIKE %(manager_contact_number)s"
            filter_query_values_count_statement += " AND manager_infos.contact_number LIKE %(manager_contact_number)s"

        if valid_param.get('manager_email', None):
            select_seller_list_statement += " AND manager_infos.email = %(manager_email)s"
            filter_query_values_count_statement += " AND manager_infos.email = %(manager_email)s"

        if valid_param.get('seller_type_name', None):
            select_seller_list_statement += " AND seller_types.name = %(seller_type_name)s"
            filter_query_values_count_statement += " AND seller_types.name = %(seller_type_name)s"

        # 데이터베이스에서는 날짜 + 시간까지 같이 검색하기 때문에 날짜에 시간을 더해줌.
        start_time = valid_param['start_time']
        close_time = valid_param['close_time']
        if start_time and close_time:
            valid_param['start_time'] = start_time + ' 00:00:00'
            valid_param['close_time'] = close_time + ' 23:59:59'
            select_seller_list_statement += " AND seller_accounts.created_at > %(start_time)s AND seller_accounts.created_at < %(close_time)s"
            filter_query_values_count_statement += " AND seller_accounts.created_at > %(start_time)s AND seller_accounts.created_at < %(close_time)s"

        # sql 명령문에 키워드 추가가 완료되면 정렬, limit, offset 쿼리문을 추가해준다.
        select_seller_list_statement += " ORDER BY seller_account_id DESC LIMIT %(limit)s OFFSET %(offset)s"

        try:
            with db_connection as db_cursor:

                # sql 쿼리와 pagination 데이터 바인딩
                db_cursor.execute(select_seller_list_statement, valid_param)
                seller_info = db_cursor.fetchall()

                # 쿼리파라미터에 excel 키가 1로 들어오면 엑셀파일을 만듦.
                if valid_param['excel'] == 1:
                    s3 = get_s3_connection()

                    # 엑셀파일로 만들경우 페이지네이션 적용을 받지않고 검색 적용만 받기 때문에 페이지네이션 부분 쿼리를 제거해준다.
                    replaced_statement = select_seller_list_statement.replace('ORDER BY seller_account_id DESC LIMIT %(limit)s OFFSET %(offset)s', '')
                    db_cursor.execute(replaced_statement, valid_param)
                    seller_info = db_cursor.fetchall()

                    # pandas 데이터 프레임을 만들기 위한 column 과 value 정리
                    seller_list_dict = {
                        '셀러번호': [seller['seller_account_id'] for seller in seller_info],
                        '관리자계정ID': [seller['login_id'] for seller in seller_info],
                        '셀러영문명': [seller['name_en'] for seller in seller_info],
                        '셀러한글명': [seller['name_kr'] for seller in seller_info],
                        '브랜디회원번호': [seller['brandi_app_user_id'] for seller in seller_info],
                        '담당자명': [seller['manager_name'] for seller in seller_info],
                        '담당자전화번호': [seller['manager_contact_number'] for seller in seller_info],
                        '판매구분': [seller['seller_type_name'] for seller in seller_info],
                        '상품개수': [seller['product_count'] for seller in seller_info],
                        '셀러URL': [seller['site_url'] for seller in seller_info],
                        '셀러등록일': [seller['created_at'] for seller in seller_info],
                        '승인여부': [seller['seller_status'] for seller in seller_info]
                    }

                    # 데이터베이스의 데이터를 기반으로 한 딕셔너리를 판다스 데이터 프레임으로 만들어줌.
                    df = pd.DataFrame(data=seller_list_dict)
                    # 첫번제 인덱스의 컬럼명을 지정해주고, 번호가 1부터 시작하도록 한다.
                    df.index.name = '번호'
                    df.index += 1

                    # 파일이름과 파일경로를 정의해줌.
                    file_name = f'{self.gen_random_name()}.xlsx'
                    file = f'../{file_name}'

                    # 파일을 엑셀파일로 변환해서 로컬에 저장
                    df.to_excel(file, encoding='utf8')

                    # 로컬에 저장된 파일을 s3에 업로드. 업로드 할 때 실패할 것을 고려하여 try-except 사용.
                    try:
                        s3.upload_file(file, "brandi-intern", file_name)
                    except Exception as e:
                        print(f'error: {e}')
                        return jsonify({'message': 'S3_UPLOAD_FAIL'}), 500

                    # s3에 올라간 파일을 다운받는 url
                    file_url = f'https://brandi-intern.s3.ap-northeast-2.amazonaws.com/{file_name}'

                    # s3에 올라간 후에 로컬에 있는 파일 삭제
                    os.remove(file)

                    return jsonify({'file_url': file_url}), 200

                # 셀러 상태를 확인하여 해당 상태에서 취할 수 있는 action 을 기존의 seller_info 에 넣어줌.
                for seller in seller_info:
                    if seller['seller_status'] == '입점':
                        seller['action'] = [
                            {'name': '휴점 신청', 'seller_status_id': 5},
                            {'name': '퇴점 신청 처리', 'seller_status_id': 4}
                        ]
                    elif seller['seller_status'] == '입점대기':
                        seller['action'] = [
                            {'name': '입점 승인', 'seller_status_id': 2},
                            {'name': '입점 거절', 'seller_status_id': 4}
                        ]
                    elif seller['seller_status'] == '휴점':
                        seller['action'] = [
                            {'name': '휴점 해제', 'seller_status_id': 2},
                            {'name': '퇴점 신청 처리', 'seller_status_id': 4}
                        ]
                    elif seller['seller_status'] == '퇴점대기':
                        seller['action'] = [
                            {'name': '휴점 신청', 'seller_status_id': 5},
                            {'name': '퇴점 확정 처리', 'seller_status_id': 4},
                            {'name': '퇴점 철회 처리', 'seller_status_id': 2}
                        ]

                # pagination 을 위해서 전체 셀러가 몇명인지 count 해서 기존의 seller_info 에 넣어줌.
                seller_count_statement = '''
                    SELECT 
                    COUNT(seller_account_id) as total_seller_count
                    FROM seller_infos
                    LEFT JOIN seller_accounts ON seller_infos.seller_account_id = seller_accounts.seller_account_no 
                    LEFT JOIN accounts ON seller_accounts.account_id = accounts.account_no 
                    WHERE close_time = '2037-12-31 23:59:59.0' AND accounts.is_deleted = 0
                '''
                db_cursor.execute(seller_count_statement)
                seller_count = db_cursor.fetchone()

                # 쿼리파라미터가 들어오면 필터된 셀러를 카운트하고 리턴 값에 포함시킨다. 쿼리파라미터가 들어오지않으면 전체 셀러 수를 포함시킴.
                db_cursor.execute(filter_query_values_count_statement, valid_param)
                filter_query_values_count = db_cursor.fetchone()
                seller_count['filtered_seller_count'] = filter_query_values_count['filtered_seller_count']

                return jsonify({'seller_list': seller_info, 'seller_count': seller_count}), 200

        # 데이터베이스 error
        except Exception as e:
            print(f'DATABASE_CURSOR_ERROR_WITH {e}')
            return jsonify({'error': 'DB_CURSOR_ERROR'}), 500

    # noinspection PyMethodMayBeStatic
    def change_seller_info(self, account_info, db_connection):

        """ 계정 셀러정보를 수정(새로운 이력 생성) INSERT INTO DB

        계정 셀러정보를 수정합니다.
        선분이력 관리를 위해 기존 셀러정보 close_time(종료일시)를 업데이트하고,
        새로운 셀러정보 이력을 생성합니다.
        입력한 브랜디 앱 아이디가 존재하는지 확인하는 절차를 가집니다.

        입점대기 상태의 셀러정보는 수정할 수 없습니다.

        기존 셀러정보와 새로운 셀러정보, 담당자 정보, 셀러 상태 변경 기록이 모두 정상 저장되어야 프로세스가 완료됩니다.
        기존 셀러정보의 종료일시를 새로운 셀러정보의 시작일시와 맞추기 위해 새로운 셀러정보를 먼저 등록했습니다.

        Args:
            account_info: 엔드포인트에서 전달 받은 account 정보
            db_connection: 연결된 database connection 객체

        Returns: http 응답코드
            200: 셀러정보 수정(새로운 이력 생성) 완료
            400: INVALID_APP_ID (존재하지 않는 브랜디 앱 아이디 입력)
                 NO_CHANGEABLE_STATUS (입점 대기 상태일때는 수정 불가)
            403: NO_AUTHORIZATION_FOR_STATUS_CHANGE
            500: DB_CURSOR_ERROR, INVALID_KEY

        Authors:
            leejm3@brandi.co.kr (이종민)

        History:
            2020-04-03 (leejm3@brandi.co.kr): 초기 생성
            2020-04-04 (leejm3@brandi.co.kr): 기본정보, 담당자정보 수정 저장 확인
            2020-04-05 (leejm3@brandi.co.kr): 에러 처리 추가 확인정
            2020-04-08 (leejm3@brandi.co.kr):
                select now() 사용하여 선분이력 관리하도록 수정
                수정 전 셀러정보 id 값을 불러오는 방식 변경
                - 기존 : request.body로 UI에게 받음
                - 변경 : DB를 조회해서 해당 seller_account_id 의 가장 마지막 셀러정보 id 를 불러옴
            2020-04-14 (leejm3@brandi.co.kr):
                - 변경하고자 하는 셀러의 아이디 값을 기존에는 parameter 로 받았는데,
                  parameter_account_no 를 기준으로 DB 에서 꺼내오도록 변경
                - 입점대기 상태일 때는 수정할 수 없도록 변경
        """
        try:
            with db_connection.cursor() as db_cursor:

                # 트랜잭션 시작
                db_cursor.execute("START TRANSACTION")
                # 자동 커밋 비활성화
                db_cursor.execute("SET AUTOCOMMIT=0")

                # list 인 manager_infos 가 SQL 에 들어가면 에러를 반환해 미리 manager_infos 에 저장하고 account_info 에서 삭제
                manager_infos = account_info['manager_infos']
                del account_info['manager_infos']

                # 현재 시간 저장
                db_cursor.execute("""
                    SELECT now()
                """)
                now = db_cursor.fetchone()

                account_info['now'] = now['now()']

                # parameter_account의 셀러 아이디 가져오기
                select_seller_account_no_statement = """
                    SELECT seller_account_no
                    FROM accounts
                    INNER JOIN
                    seller_accounts
                    ON accounts.account_no = seller_accounts.account_id
                    WHERE accounts.account_no = %(parameter_account_no)s
                """

                db_cursor.execute(select_seller_account_no_statement, account_info)
                seller_account_result = db_cursor.fetchone()

                # 셀러계정 아이디 저장
                account_info['seller_account_id'] = seller_account_result['seller_account_no']

                # 이전 셀러정보 아이디 가져오기
                # seller_infos 테이블 SELECT
                select_seller_infos_statement = """
                    SELECT seller_info_no
                    FROM seller_infos
                    WHERE seller_account_id = %(seller_account_id)s
                    AND close_time = '2037-12-31 23:59:59'
                """

                db_cursor.execute(select_seller_infos_statement, account_info)

                previous_seller_info_id = db_cursor.fetchone()

                account_info['previous_seller_info_id'] = previous_seller_info_id['seller_info_no']

                # 브랜디앱유저 검색 정보
                brandi_app_user_data = {
                    'app_id': account_info['brandi_app_user_app_id']
                }

                # brandi_app_users 테이블 SELECT
                select_app_id_statement = """
                    SELECT
                    app_user_no
                    FROM
                    brandi_app_users
                    WHERE app_id = %(app_id)s
                    AND is_deleted = 0
                """

                db_cursor.execute(select_app_id_statement, brandi_app_user_data)

                # app_id 출력 결과 저장
                app_id_result = db_cursor.fetchone()

                # app_id가 있으면 account_info 에 app_user_no 저장
                if app_id_result:
                    account_info['app_user_no'] = app_id_result['app_user_no']

                # app_id가 없으면 app_id가 존재하지 않는다고 리턴
                else:
                    return jsonify({'message': 'INVALID_APP_ID'}), 400

                # 셀러 기본 정보 생성
                # seller_infos 테이블 INSERT INTO
                insert_seller_info_statement = """
                    INSERT INTO seller_infos (
                    seller_account_id,
                    profile_image_url,
                    seller_status_id,
                    seller_type_id,
                    product_sort_id,                 
                    name_kr,
                    name_en,
                    brandi_app_user_id,
                    ceo_name,
                    company_name,
                    business_number,
                    certificate_image_url,
                    online_business_number,
                    online_business_image_url,
                    background_image_url,
                    short_description,
                    long_description,
                    site_url,
                    kakao_id,
                    insta_id,
                    yellow_id,
                    center_number,
                    zip_code,
                    address,
                    detail_address,
                    weekday_start_time,
                    weekday_end_time,
                    weekend_start_time,
                    weekend_end_time,
                    bank_name,
                    bank_holder_name,
                    account_number,
                    modifier,
                    start_time
                ) VALUES (
                    %(seller_account_id)s,
                    %(profile_image_url)s,
                    %(seller_status_no)s,
                    %(seller_type_no)s,
                    (SELECT product_sort_id FROM seller_types WHERE seller_type_no = %(seller_type_no)s),                     
                    %(name_kr)s,
                    %(name_en)s,
                    %(app_user_no)s,                    
                    %(ceo_name)s,
                    %(company_name)s,
                    %(business_number)s,
                    %(certificate_image_url)s,
                    %(online_business_number)s,
                    %(online_business_image_url)s,
                    %(background_image_url)s,
                    %(short_description)s,
                    %(long_description)s,
                    %(site_url)s,
                    %(kakao_id)s,
                    %(insta_id)s,
                    %(yellow_id)s,                    
                    %(center_number)s,
                    %(zip_code)s,
                    %(address)s,
                    %(detail_address)s,
                    %(weekday_start_time)s,
                    %(weekday_end_time)s,
                    %(weekend_start_time)s,
                    %(weekend_end_time)s,
                    %(bank_name)s,
                    %(bank_holder_name)s,
                    %(account_number)s,
                    %(decorator_account_no)s,
                    %(now)s
                )"""

                # 셀러 기본정보 insert 함
                db_cursor.execute(insert_seller_info_statement, account_info)

                # 위에서 생성된 새로운 셀러정보의 id 값을 가져옴
                seller_info_no = db_cursor.lastrowid

                # manager_infos 테이블 INSERT INTO
                insert_manager_info_statement = """
                    INSERT INTO manager_infos (
                    name,
                    contact_number,
                    email,
                    ranking,
                    seller_info_id
                ) VALUES (
                    %(name)s,
                    %(contact_number)s,
                    %(email)s,
                    %(ranking)s,
                    %(seller_info_id)s
                )"""

                # for 문을 돌면서 담당자 정보를 insert 함
                for i in range(len(manager_infos)):
                    manager_info_data = {
                        'name': manager_infos[i]['name'],
                        'contact_number': manager_infos[i]['contact_number'],
                        'email': manager_infos[i]['email'],
                        'ranking': manager_infos[i]['ranking'],
                        'seller_info_id': seller_info_no
                    }

                    db_cursor.execute(insert_manager_info_statement, manager_info_data)

                # 이전 셀러정보 수정일시, 종료일시 업데이트
                # previous_seller_info 테이블 UPDATE
                update_previous_seller_info_statement = """
                    UPDATE seller_infos
                    SET
                    close_time = %(now)s
                    WHERE seller_info_no = %(previous_seller_info_id)s
                """

                db_cursor.execute(update_previous_seller_info_statement, account_info)

                # 이전 셀러정보의 셀러 상태값 가져오기
                select_previous_seller_status_statement = """
                    SELECT seller_status_id
                    FROM seller_infos
                    WHERE seller_info_no = %(previous_seller_info_id)s
                """

                db_cursor.execute(select_previous_seller_status_statement, account_info)

                previous_seller_status_id = db_cursor.fetchone()

                account_info['previous_seller_status_id'] = previous_seller_status_id['seller_status_id']

                # 입점대기 상태일 때는 셀러정보를 수정할 수 없음
                if account_info['previous_seller_status_id'] == 1:
                    return jsonify({'message': 'NO_CHANGEABLE_STATUS'}), 400

                # 이전 셀러정보의 셀러 상태값과 새로운 셀러정보의 셀러 상태값이 다르면, 셀러 상태정보이력 테이블 INSERT INTO
                if account_info['previous_seller_status_id'] != account_info['seller_status_no']:

                    # 마스터 권한이 아닐 때 셀러 상태(입점 등)를 변경하려고 하면 에러 리턴
                    if account_info['auth_type_id'] != 1:
                        return jsonify({'message': 'NO_AUTHORIZATION_FOR_STATUS_CHANGE'}), 403

                    # INSERT INTO 문에서 확인할 데이터
                    seller_status_data = {
                        'seller_account_id': account_info['seller_account_id'],
                        'new_seller_info_no': seller_info_no,
                        'seller_status_id': account_info['seller_status_no'],
                        'modifier': account_info['decorator_account_no'],
                        'now': now['now()']
                    }

                    # seller_status_change_histories 테이블 INSERT INTO
                    insert_status_history_statement = """
                        INSERT INTO seller_status_change_histories (
                        seller_account_id,
                        changed_time,
                        seller_status_id,
                        modifier
                    ) VALUES (
                        %(seller_account_id)s,
                        %(now)s,
                        %(seller_status_id)s,
                        %(modifier)s
                    )"""

                    db_cursor.execute(insert_status_history_statement, seller_status_data)

                db_connection.commit()
                return jsonify({'message': 'SUCCESS'}), 200

        except KeyError as e:
            print(f'KEY_ERROR WITH {e}')
            return jsonify({'message': 'INVALID_KEY'}), 500

        except Error as e:
            print(f'DATABASE_CURSOR_ERROR_WITH {e}')
            db_connection.rollback()
            return jsonify({'message': 'DB_CURSOR_ERROR'}), 500

    # noinspection PyMethodMayBeStatic
    def change_seller_status(self, target_seller_info, db_connection):

        """ 마스터 권한 셀러 상태 변경
        마스터 권한을 가진 유저가 데이터베이스의 셀러의 상태를 변경함.
        seller_infos 테이블에 새로운 이력(row)를 생성하고 seller_infos 의 foreign key 룰 가지는
        manager_infos 테이블에도 새로운 셀러 정보 이력을 foreign key 로 가지도록 row 를 추가해줌.
        마지막으로 seller_status_change_histories 테이블에 변경 이력을 추가해줌.

            Args:
                target_seller_info: 바꾸고자 하는 셀러의 정보
                db_connection: 데이터베이스 커넥션 객체

            Returns:
                200: 셀러 상태 정보 수정 성공
                500: 데이터베이스 error, key error

            Authors:
                yoonhc@brandi.co.kr (윤희철)

            History:
                2020-04-05 (yoonhc@brandi.co.kr): 초기 생성
                2020-04-09 (yoonhc@brandi.co.kr): 셀러정보 선분이력 반영
                2020-04-13 (yoonhc@brandi.co.kr): 셀러 상태를 변경하면 seller_status_change_histories 테이블에 row 추가.

        """

        # 데이터베이스 커서 실행
        try:
            with db_connection as db_cursor:

                # 트랜잭션 시작
                db_cursor.execute("START TRANSACTION")

                # 자동 커밋 비활성화
                db_cursor.execute("SET AUTOCOMMIT=0")

                # 새로운 이력 생성 이전의 셀러 정보를 가져옴
                db_cursor.execute('''
                SELECT 
                    seller_info_no, seller_status_id
                
                FROM 
                    seller_infos
                                
                WHERE 
                    seller_account_id = %(seller_account_id)s
                    AND close_time = '2037-12-31 23:59:59'
                    AND is_deleted = 0
                ''', target_seller_info)

                # 가져온 셀러정보를 타겟셀러 정보를 변수화
                previous_seller_info = db_cursor.fetchone()

                # 요청으로 들어온 상태값이랑 데이터베이스에 있는 타겟 셀러 정보의 상태값이 같은지 확인
                if previous_seller_info['seller_status_id'] == target_seller_info['seller_status_id']:
                    return jsonify({'message': 'INVALID_ACTION'}), 400

                # 새로운 버전 이전의 버전의 셀러 번호를 target_seller_info 에 저장장
                target_seller_info['previous_seller_info_no'] = previous_seller_info['seller_info_no']

                # seller_infos : 셀러 상태 변경 sql 명령문, select 와 insert 를 같이 사용해서 기존에 있던 정보를 그대로 새로운 row 에 추가사킴
                update_seller_status_statement = """
                    INSERT INTO seller_infos
                    (
                        seller_account_id,
                        profile_image_url,
                        seller_status_id,
                        seller_type_id,
                        product_sort_id,                 
                        name_kr,
                        name_en,
                        brandi_app_user_id,
                        ceo_name,
                        company_name,
                        business_number,
                        certificate_image_url,
                        online_business_number,
                        online_business_image_url,
                        background_image_url,
                        short_description,
                        long_description,
                        site_url,
                        kakao_id,
                        insta_id,
                        yellow_id,
                        center_number,
                        zip_code,
                        address,
                        detail_address,
                        weekday_start_time,
                        weekday_end_time,
                        weekend_start_time,
                        weekend_end_time,
                        bank_name,
                        bank_holder_name,
                        account_number,
                        modifier
                    )
                    SELECT
                        seller_account_id,
                        profile_image_url,
                        %(seller_status_id)s,
                        seller_type_id,
                        product_sort_id,                 
                        name_kr,
                        name_en,
                        brandi_app_user_id,
                        ceo_name,
                        company_name,
                        business_number,
                        certificate_image_url,
                        online_business_number,
                        online_business_image_url,
                        background_image_url,
                        short_description,
                        long_description,
                        site_url,
                        kakao_id,
                        insta_id,
                        yellow_id,
                        center_number,
                        zip_code,
                        address,
                        detail_address,
                        weekday_start_time,
                        weekday_end_time,
                        weekend_start_time,
                        weekend_end_time,
                        bank_name,
                        bank_holder_name,
                        account_number,
                        %(modifier)s
                    FROM 
                        seller_infos                    
                    WHERE
                        seller_account_id = %(seller_account_id)s 
                    AND 
                        close_time = '2037-12-31 23:59:59'
                    AND
                        is_deleted = 0
                """

                # seller_infos: 데이터 sql 명령문과 셀러 데이터 바인딩 후 새로운 셀러 정보 이력의 primary key 딕셔너리에 담음
                db_cursor.execute(update_seller_status_statement, target_seller_info)
                new_seller_info_id = db_cursor.lastrowid
                target_seller_info['new_seller_info_id'] = new_seller_info_id

                # 선분이력을 닫아주는 시간을 쿼리로 가져옴. 선분이력을 닫아주는 시간을 타겟 셀러 정보에 저장함.
                db_cursor.execute('SELECT NOW()')
                close_time = db_cursor.fetchone()
                target_seller_info['close_time'] = close_time['NOW()']

                # seller_infos 테이블에 해당 seller_account 의 새로운 이력이 생겼기 때문에 이전의 이력을 끊어주는 작업.
                update_previous_seller_infos_stat = '''
                    UPDATE
                    seller_infos
                    SET
                    close_time = %(close_time)s
                    WHERE
                    seller_info_no = %(previous_seller_info_no)s
                    AND seller_account_id = %(seller_account_id)s
                '''
                db_cursor.execute(update_previous_seller_infos_stat, target_seller_info)

                # manager_infos: 매니저 정보에서 셀러 인포 foreign key 를 새로 생성된 이력으로 바꿔주는 명령문.
                insert_manager_info_statement = """
                    INSERT INTO manager_infos (
                        name,
                        contact_number,
                        email,
                        ranking,
                        seller_info_id
                    ) 
                    SELECT
                        name,
                        contact_number,
                        email,
                        ranking,
                        %(new_seller_info_id)s
                        FROM manager_infos
                        WHERE seller_info_id = %(previous_seller_info_no)s
                """
                db_cursor.execute(insert_manager_info_statement, target_seller_info)

                # 셀러 변경 이력 테이블에 새로운 row 추가
                db_cursor.execute('''
                INSERT INTO seller_status_change_histories(
                        seller_account_id,
                        changed_time,
                        seller_status_id,
                        modifier
                ) VALUES (
                        %(seller_account_id)s,
                        %(close_time)s,
                        %(seller_status_id)s,
                        %(modifier)s
                )
                ''', target_seller_info)

                db_connection.commit()
                return jsonify({'message': 'SUCCESS'}), 200

        except KeyError as e:
            print(f'KEY_ERROR WITH {e}')
            return jsonify({'message': 'INVALID_KEY'}), 500

        except Error as e:
            print(f'DATABASE_CURSOR_ERROR_WITH {e}')
            db_connection.rollback()
            return jsonify({'message': 'DB_CURSOR_ERROR'}), 500

    # noinspection PyMethodMayBeStatic
    def get_account_info(self, account_info, db_connection):

        """ 로그인 정보 확인

        account_info 를 통해서 DB 에 있는 특정 계정 정보의 account_no 와 암호화 되어있는 password 를 가져와서 return

        Args:
            account_info: 유효성 검사를 통과한 account 정보 (login_id, password)
            db_connection: 연결된 database connection 객체

        Returns:
            200: db_account_info db 에서 get 한 account_no 와 password
            400: INVALID_KEY
            500: DB_CURSOR_ERROR

        Authors:
            choiyj@brandi.co.kr (최예지)
            leejm3@brandi.co.kr (이종민)

        History:
            2020-04-05 (choiyj@brandi.co.kr): 초기 생성
            2020-04-05 (choiyj@brandi.co.kr): SQL 문을 통해 DB 에서 원하는 정보를 가지고 와서 return 하는 함수 구현
            2020-04-16 (leejm3@brandi.co.kr): 로그인 시 입점대기 여부를 확인하기 위해 상태 정보 셀렉트 추가
        """

        try:
            # db_cursor 는 db_connection 에 접근하는 본체 (가져온 정보는 cursor 가 가지고 있다)
            with db_connection as db_cursor:

                # sql 문 작성 (원하는 정보를 가져오거나 집어넣거나)
                select_account_info_statement = """
                    SELECT
                        AC01.account_no,
                        AC01.password,
                        AC03.seller_status_id
                    
                    FROM 
                        accounts as AC01
                    
                    LEFT JOIN
                        seller_accounts as AC02
                        ON AC01.account_no = AC02.account_id
                        
                    LEFT JOIN
                        seller_infos as AC03
                        ON AC02.seller_account_no = AC03.seller_account_id
                                        
                    WHERE 
                        AC01.login_id = %(login_id)s 
                        AND AC01.is_deleted = 0
                        AND AC03.close_time = '2037-12-31 23:59:59'
                """

                # SELECT 문 실행
                db_cursor.execute(select_account_info_statement, account_info)

                # DB 에 저장하는 로직 작성 (fetchone, fetchall, fetchmany)
                account_info_result = db_cursor.fetchone()

                # DB 에서 꺼내온 정보를 return
                return account_info_result

        except KeyError as e:
            print(f'KEY_ERROR WITH {e}')
            return jsonify({'message': 'INVALID_KEY'}), 400

        except Error as e:
            print(f'DATABASE_CURSOR_ERROR_WITH {e}')
            return jsonify({'message': 'DB_CURSOR_ERROR'}), 500

    # noinspection PyMethodMayBeStatic
    def check_overlap_login_id(self, login_id, db_connection):

        """ 로그인 아이디 중복 체크

        service 에서 전달 받은 login_id 가 DB에 존재하는지 확인해서 리턴

        Args:
            login_id: account_info 의 login_id
            db_connection: 연결된 database connection 객체

        Returns:
            login_id로 확인된 계정 번호.
            -> service 에서 계정번호가 검색된 경우 중복처리 진행
            500: DB_CURSOR_ERROR

        Authors:
            leejm3@brandi.co.kr (이종민)

        History:
            2020-04-06 (leejm3@brandi.co.kr): 초기 생성

        """

        try:
            with db_connection.cursor() as db_cursor:

                # 계정 SELECT 문
                select_account_statement = """
                    SELECT
                        account_no
                    
                    FROM
                        accounts
                    
                    WHERE
                        login_id = %(login_id)s
                """

                # service 에서 넘어온 셀러 데이터
                login_id_data = {
                    'login_id': login_id
                }

                # 데이터 sql 명령문과 셀러 데이터 바인딩
                db_cursor.execute(select_account_statement, login_id_data)

                # 쿼리로 나온 계정번호를 저장
                select_result = db_cursor.fetchone()
                return select_result

        # 데이터베이스 error
        except Exception as e:
            print(f'DAO_DATABASE_CURSOR_ERROR_WITH {e}')
            return jsonify({'error': 'DB_CURSOR_ERROR'}), 500

    # noinspection PyMethodMayBeStatic
    def check_overlap_name_kr(self, name_kr, db_connection):
        """ 셀러명 중복 체크

        service 에서 전달 받은 name_kr 가 DB에 존재하는지 확인해서 리턴

        Args:
            name_kr: account_info 의 name_kr
            db_connection: 연결된 database connection 객체

        Returns:
            name_kr로 확인된 셀러정보 번호.
                -> service 에서 셀러정보 번호가 검색된 경우 중복처리 진행
            500: INVALID_KEY, DB_CURSOR_ERROR

        Authors:
            leejm3@brandi.co.kr (이종민)

        History:
            2020-04-06 (leejm3@brandi.co.kr): 초기 생성

        """

        try:
            with db_connection.cursor() as db_cursor:

                # 셀러정보 SELECT 문
                select_seller_info_statement = """
                    SELECT
                        seller_info_no
                    
                    FROM
                        seller_infos
                    
                    WHERE
                        name_kr = %(name_kr)s
                        AND is_deleted = 0
                """

                # service 에서 넘어온 셀러 데이터
                name_kr_data = {
                    'name_kr': name_kr
                }

                # 데이터 sql 명령문과 셀러 데이터 바인딩
                db_cursor.execute(select_seller_info_statement, name_kr_data)

                # 쿼리로 나온 셀러정보 번호를 저장
                select_result = db_cursor.fetchone()
                return select_result

        except KeyError as e:
            print(f'KEY_ERROR_WITH {e}')
            db_connection.rollback()
            return jsonify({'message': 'INVALID_KEY'}), 500

        except Exception as e:
            print(f'DATABASE_CURSOR_ERROR_WITH {e}')
            return jsonify({'error': 'DB_CURSOR_ERROR'}), 500

    # noinspection PyMethodMayBeStatic
    def check_overlap_name_en(self, name_en, db_connection):
        """ 셀러 영문명 중복 체크

        service 에서 전달 받은 name_en 가 DB에 존재하는지 확인해서 리턴

        Args:
            name_en: account_info 의 name_en
            db_connection: 연결된 database connection 객체

        Returns:
            200:name_en로 확인된 셀러정보 번호.
                -> service 에서 셀러정보 번호가 검색된 경우 중복처리 진행
            500: DB_CURSOR_ERROR, INVALID_KEY

        Authors:
            leejm3@brandi.co.kr (이종민)

        History:
            2020-04-06 (leejm3@brandi.co.kr): 초기 생성

        """

        try:
            with db_connection.cursor() as db_cursor:

                # 셀러정보 SELECT 문
                select_seller_info_statement = """
                    SELECT
                        seller_info_no
                    
                    FROM
                        seller_infos
                    
                    WHERE
                        name_en = %(name_en)s
                        AND is_deleted = 0
                """

                # service 에서 넘어온 셀러 데이터
                name_en_data = {
                    'name_en': name_en
                }

                # 데이터 sql 명령문과 셀러 데이터 바인딩
                db_cursor.execute(select_seller_info_statement, name_en_data)

                # 쿼리로 나온 셀러정보 번호를 저장
                select_result = db_cursor.fetchone()
                return select_result

        except KeyError as e:
            print(f'KEY_ERROR_WITH {e}')
            db_connection.rollback()
            return jsonify({'message': 'INVALID_KEY'}), 500

        except Exception as e:
            print(f'DATABASE_CURSOR_ERROR_WITH {e}')
            return jsonify({'error': 'DB_CURSOR_ERROR'}), 500

    # noinspection PyMethodMayBeStatic
    def sign_up(self, account_info, db_connection):

        """ 계정 회원가입 데이터를 INSERT 하는 DAO

        1. accounts 계정 생성
        2. seller_accounts 셀러 계정 생성
        3. seller_infos 셀러 정보 생성
        4. manage_infos 담당자 정보 생성
        5. seller_status_change_histories 셀러 상태 변경 이력 생성

        Args:
            account_info: 유효성 검사를 통과한 account 정보
                login_id 로그인 아이디
                password 암호화된 비밀번호
                contact_number 담당자 번호
                seller_type_id 셀러 속성 아이디
                name_kr 셀러명
                name_en 셀러 영문명
                center_number 고객센터 번호
                site_url 사이트 URL
                kakao_id 카카오 아이디
                insta_id 인스타 아이디
            db_connection: 연결된 database connection 객체

        Returns: http 응답코드
            200: SUCCESS 셀러 회원가입 완료
            500: INVALID_KEY, DB_CURSOR_ERROR

        Authors:
            leejm3@brandi.co.kr (이종민)

        History:
            2020-04-01 (leejm3@brandi.co.kr) : 초기 생성
            
        """

        try:
            with db_connection.cursor() as db_cursor:

                # accounts 생성
                # 계정 INSERT 문
                insert_accounts_statement = """
                    INSERT INTO accounts(
                        auth_type_id,
                        login_id,
                        password
                ) VALUES (
                        2,
                        %(login_id)s,
                        %(password)s
                )"""

                # 데이터 sql 명령문과 셀러 데이터 바인딩
                db_cursor.execute(insert_accounts_statement, account_info)

                # 위에서 생성된 새로운 계정의 id 값을 가져옴
                account_no = db_cursor.lastrowid
                account_info['account_no'] = account_no
                # seller_accounts 생성
                # 셀러계정 INSERT 문
                insert_seller_accounts_statement = """
                    INSERT INTO seller_accounts(
                    account_id
                ) VALUES (
                    %(account_no)s
                )"""

                # 데이터 sql 명령문과 셀러 데이터 바인딩
                db_cursor.execute(insert_seller_accounts_statement, account_info)

                # 위에서 생성된 셀러계정의 id 값을 가져옴
                seller_account_no = db_cursor.lastrowid
                account_info['seller_account_id'] = seller_account_no

                # seller_infos 생성
                # 셀러정보 INSERT 문
                insert_seller_infos_statement = """
                    INSERT INTO seller_infos(
                        seller_account_id,
                        seller_type_id,
                        seller_status_id,
                        product_sort_id,
                        name_kr,
                        name_en,
                        center_number,
                        site_url,
                        kakao_id,
                        insta_id,
                        modifier
                ) VALUES (
                        %(seller_account_id)s,
                        %(seller_type_id)s,
                        1,
                        (SELECT product_sort_id FROM seller_types WHERE seller_type_no = %(seller_type_id)s),
                        %(name_kr)s,
                        %(name_en)s,
                        %(center_number)s,
                        %(site_url)s,
                        %(kakao_id)s,
                        %(insta_id)s,
                        %(account_no)s
                )"""

                # 데이터 sql 명령문과 셀러 데이터 바인딩
                db_cursor.execute(insert_seller_infos_statement, account_info)

                # 위에서 생성된 셀러정보의 id 값을 가져옴
                seller_info_no = db_cursor.lastrowid
                account_info['seller_info_no'] = seller_info_no

                # manager_infos 생성
                # 담당자정보 INSERT 문
                insert_manager_infos_statement = """
                    INSERT INTO manager_infos(
                        contact_number,
                        seller_info_id
                ) VALUES (
                        %(contact_number)s,
                        %(seller_info_no)s
                )"""

                # 데이터 sql 명령문과 셀러 데이터 바인딩
                db_cursor.execute(insert_manager_infos_statement, account_info)

                # seller_status_change_histories 생성
                # 셀러 상태변경 이력 INSERT 문
                insert_status_histories_statement = """
                    INSERT INTO seller_status_change_histories(
                        seller_account_id,
                        seller_status_id,
                        modifier                    
                ) VALUES (
                        %(seller_account_id)s,
                        1,
                        %(account_no)s
                )"""

                # 데이터 sql 명령문과 셀러 데이터 바인딩
                db_cursor.execute(insert_status_histories_statement, account_info)
                db_connection.commit()
                return jsonify({"message": "SUCCESS"}), 200

        except KeyError as e:
            print(f'KEY_ERROR_WITH {e}')
            db_connection.rollback()
            return jsonify({'message': 'INVALID_KEY'}), 500

        except Error as e:
            print(f'DATABASE_CURSOR_ERROR_WITH {e}')
            db_connection.rollback()
            return jsonify({'message': 'DB_CURSOR_ERROR'}), 500
