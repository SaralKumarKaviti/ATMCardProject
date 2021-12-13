from mongoengine import connect

client = connect('atmdata',host='localhost',port=27017)