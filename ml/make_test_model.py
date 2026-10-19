"""ml/make_test_model.py —— CI 离线生成小型确定性测试模型（不进入正式交付）"""

import pathlib
import sys

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

X = [
    "free win prize call now",
    "claim your reward",
    "urgent winner selected",
    "see you at dinner",
    "ok call me later",
    "meeting moved to 3pm",
]
y = ["spam", "spam", "spam", "ham", "ham", "ham"]
pipe = Pipeline([("tfidf", TfidfVectorizer()), ("clf", MultinomialNB())])
pipe.fit(X, y)
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "models/test_model.joblib")
joblib.dump(pipe, out)
print("written:", out)
