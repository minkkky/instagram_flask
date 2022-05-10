import codecs

from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
from werkzeug.utils import secure_filename

from pymongo import MongoClient

import jwt
import hashlib

client = MongoClient('#################')
db = client.instaClone

#Flask 객체 인스턴스 생성
app = Flask(__name__)

@app.route('/api/feed', methods=["POST"])
def upload():
    images = request.files.getlist("image[]")
    desc = request.form['desc']
    location = request.form['location']
    time = datetime.now()
    email = "LULULALA_2@insta.com"
    user_id = "LULULALA_2"
    images_path = []

    for image in images:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        path = './static/img/post_img/' + timestamp + secure_filename(image.filename)
        print(path)
        image.save(path)
        images_path.append(path)

    doc = {
        'email': email,
        'user_id': user_id,
        'photo': images_path,
        'location': location,
        'post_date': time,
        'desc': desc
    }

    db.posts.insert_one(doc)

    return jsonify({'msg': '완료!'})


@app.route('/feed', methods=['GET'])
def getFeed():
  # 피드 조회하기
  posts = list(db.posts.find({}).sort('post_date', -1).limit(20))

  for post in posts:
    post["_id"] = str(post["_id"])

  return jsonify({'posts': posts, 'result': 'success'})


@app.route('/api/comment', methods=['GET'])
def getComment():
  # 댓글 조회하기
  post_id = request.args['post_id_give']
  all_comments = list(db.comments.find({'post_id': post_id}))

  for comment in all_comments:
    comment["_id"] = str(comment["_id"])
    user_info = db.users.find_one({"email": comment['email']})
    comment['user_id'] = user_info['user_id']

  return jsonify({'comments': all_comments})


@app.route('/api/comment', methods=['POST'])
def postComment():
  # 댓글 작성하기
  # user_info = db.users.find_one({"email": 'LULULALA_2@insta.com'})
  post_id_receive = request.form['post_id_give']
  comment_receive = request.form['comment_give']
  cmt_date_receive = request.form['cmt_date_give']

  doc = {'post_id': post_id_receive, 'email': 'LULULALA_2@insta.com', 'comment': comment_receive, 'cmt_date': cmt_date_receive}
  db.comments.insert_one(doc)

  return jsonify({'msg': '댓글 작성 완료!'})


# @app.route('/api/like', methods=['POST'])
# def updateLike():
#   # 좋아요 업데이트
#
#   user_info = db.users.find_one({'email': 'LULUALA_2@insta.com'})
#   post_id_receive = request.form['post_id_give']
#   action_receive = request.form['action_give']
#
#   doc = {'post_id': post_id_receive,
#          'user_id': user_info['user_id']}
#
#   if action_receive == "like":
#     db.likes.insert_one(doc)
#   else:
#     db.likes.delete_one(doc)
#
#   count = db.likes.count_documents({"post_id": post_id_receive})
#   return jsonify({'result': 'success', 'msg': 'updated', 'count':count})


if __name__=="__main__":
  app.run(debug=True)
  # host 등을 직접 지정하고 싶다면
  # app.run(host="127.0.0.1", port="5000", debug=True)

SECRET_KEY = 'CMG'

@app.route('/')
def home():
   token_receive = request.cookies.get('mytoken')

   # try뜻
   try:
      # jwt 디코드(암호풀기를 해준다 jwt토큰 안에 있는 토큰 리시브 시크릿키) 까지는 알겠는데 헤쉬256이 , 하고 나오는 이유는 모르겠다
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      # payload의 뜻 알기, 이 코드는 db에 저장되어 있는 id 값을 불러오는 코드인듯?
      user_info = db.user.find_one({"id": payload['id']})
      # render_template()뜻 알기
      return render_template('index.html')
   except jwt.ExpiredSignatureError:
      return render_template('login_page.html')
      # return redirect(url_for("login", msg="로그인 시간이 만료되었습니다"))
   except jwt.exceptions.DecodeError:
      return render_template('login_page.html')
      # return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다"))


@app.route('/signup')
def home_signup():
   return render_template('sign_up.html')

# @app.route('/loginpage')
# def home_signup():
#    return render_template('login_page.html')


@app.route('/signupPrac/', methods=['POST'])
def sign_up_post():
   email_receive = request.form['email_give']
   id_receive = request.form['id_give']
   name_receive = request.form['name_give']
   password_receive = request.form['password_give']

   pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

   doc = {
      'email': email_receive,
      'id': id_receive,
      'name': name_receive,
      'password': pw_hash
   }
   db.users.insert_one(doc)
   return jsonify({'msg': '가입완료'})


@app.route('/api/login', methods=['POST'])
def api_login():
   id_receive = request.form['id_give']
   password_receive = request.form['pw_give']
   pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
   result = db.users.find_one({'email': id_receive, 'password': pw_hash})

   if result is not None:
      payload = {
         'id': id_receive,
         'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=30)
      }
      token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')


      return jsonify({'result': 'success', 'token': token})
   else:
      return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# get을 받는 이유
@app.route('/signupPrac', methods=['GET'])
def sing_up_get():
   token_receive = request.cookies.get('mytoken')
   try:
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      print(payload)

      userinfo = db.users.find_one({'id': payload['id']})
      return jsonify({'result': 'success', 'nickname': userinfo['nick']})
   except jwt.ExpiredSignatureError:
      return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다'})
   except jwt.ExpiredSignatureError:
      return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다'})

   # return jsonify({'result':'success', 'msg': '이 요청은 GET!'})

if __name__ == '__main__':
   app.run('0.0.0.0', port=5000, debug=True)
