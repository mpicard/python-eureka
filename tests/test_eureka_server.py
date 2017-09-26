import requests


headers = {'Content-Type': 'application/json'}


def test_eureka_server_conn():
    r = requests.get('http://eureka:8080/eureka/v2/apps',
                     headers={'accept': 'application/json'})
    print(r.json())
    assert r.ok
