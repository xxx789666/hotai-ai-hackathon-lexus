"""傳統機器學習對照實驗。固定 seed 42，重用 r4 的 make_split 與同一份標籤。

  python pipeline/baseline_ml.py
  python pipeline/baseline_ml.py --models logreg,keyword --features f1 --balances a

只使用 sklearn（不裝 jieba、不呼叫雲端 LLM、不使用 GPU）。
結果寫到 data/processed/baseline_ml_results.json（data/ 不進 repo）。
超參只看驗證集；測試集只在每個模型選定後評估一次。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import LinearSVC, SVC
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.utils.class_weight import compute_sample_weight

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "local_jev"))
sys.path.insert(0, str(ROOT / "pipeline"))
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from evaluate import cohen_kappa, prf_counts  # noqa: E402
from train_churn_lora import (  # noqa: E402
    c_dist,
    make_split,
    oversample_pos_fraction,
    subsample_neg_multiple,
)
from verify_churn import build_context, load_jsonl  # noqa: E402

P = ROOT / "data" / "processed"
SEED = 42
N_BOOT = 1000
SVD_DIM = 300
MAX_FEATURES = 80000

# T8 表。核對不一致就停止，避免拿錯切分訓練。
EXPECTED = {
    "train": {"n": 9431, "docs": 1655, "c": {"0": 8127, "1": 784, "2": 363, "3": 157}},
    "val": {"n": 1096, "docs": 184, "c": {"0": 992, "1": 70, "2": 28, "3": 6}},
    "test": {"n": 600, "docs": 421, "c": {"0": 463, "1": 72, "2": 39, "3": 26}},
}
EXPECTED_SAMPLED = {"0": 1404, "1": 156, "2": 715, "3": 325, "n": 2600, "pos": 1040, "neg": 1560}

# 詞表來自流失標註定義（考慮離開／已離開），不是從測試集挖出來的。
AFTERSALES = [
    "保養", "維修", "保固", "原廠", "服務廠", "外廠", "保養廠", "工時", "工資",
    "零件", "機油", "回廠", "進廠", "定保", "小保養", "大保養", "和泰",
]
CHURN = [
    "不回原廠", "不再回原廠", "不再去原廠", "不去原廠", "不回廠", "不回服務廠",
    "不回和泰", "離開原廠", "不進原廠", "不給原廠", "不給和泰",
    "改去外廠", "去外廠", "找外廠", "給外廠", "送外廠", "外廠保養", "外廠修",
    "自己動手", "自己保養", "自己修", "自己換", "自己處理",
    "自備零件", "自備機油", "自備料", "自備",
    "路邊廠", "私人廠", "非原廠", "外面修", "外面保養",
    "不想回", "懶得回", "不回了", "不回去", "不再回去", "沒再回",
    "以後不去", "下次不去", "不想保", "不保了",
    "另找", "找別家", "別家保養",
    "賣掉", "賣車",
]
LEFT = [
    "不再回原廠", "不再去原廠", "不再回去", "沒再回", "不回了", "不保了",
    "賣掉", "賣車", "離開原廠",
]
COMPLAINT = ["太貴", "很貴", "態度", "等很久", "等待", "亂收", "不專業", "品質", "推銷", "抱怨"]

MODEL_NAMES = [
    "logreg", "linearsvc", "rbfsvc", "dt_clf", "dt_reg", "rf", "hgb", "knn", "keyword",
]
DENSE_MODELS = {"rbfsvc", "hgb"}


def log(msg: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {msg}", flush=True)


def dist_ok(got: dict, exp: dict) -> bool:
    return all(int(got.get(k, -1)) == v for k, v in exp.items())


def check_split(split: dict, sampled: list[str]) -> dict:
    labels = split["labels"]
    report = {
        "train": {"n": len(split["train_sids"]), "docs": split["n_docs_train"], "c": c_dist(split["train_sids"], labels)},
        "val": {"n": len(split["val_sids"]), "docs": split["n_docs_val"], "c": c_dist(split["val_sids"], labels)},
        "test": {"n": len(split["test_sids"]), "docs": split["n_docs_test"], "c": c_dist(split["test_sids"], labels)},
        "missing_test_doc": len(split["missing_test_doc"]),
        "sampled_c": c_dist(sampled, labels),
    }
    problems = []
    for name in ("train", "val", "test"):
        got, exp = report[name], EXPECTED[name]
        if got["n"] != exp["n"] or got["docs"] != exp["docs"] or not dist_ok(got["c"], exp["c"]):
            problems.append(f"{name}: got n={got['n']} docs={got['docs']} c={got['c']} expected n={exp['n']} docs={exp['docs']} c={exp['c']}")
    if report["missing_test_doc"] != 0:
        problems.append(f"missing_test_doc={report['missing_test_doc']}")
    sc = report["sampled_c"]
    pos = sc.get("2", 0) + sc.get("3", 0)
    neg = sc.get("0", 0) + sc.get("1", 0)
    report["sampled_pos"] = pos
    report["sampled_neg"] = neg
    if sc.get("n") != EXPECTED_SAMPLED["n"] or pos != EXPECTED_SAMPLED["pos"] or neg != EXPECTED_SAMPLED["neg"] or not dist_ok(sc, {k: EXPECTED_SAMPLED[k] for k in "0123"}):
        problems.append(f"r4 recipe: got {sc} pos={pos} neg={neg} expected {EXPECTED_SAMPLED}")
    report["ok"] = not problems
    report["problems"] = problems
    return report


def binary_y(sids, labels) -> np.ndarray:
    return np.asarray([int(int(labels[s]["c"]) >= 2) for s in sids], dtype=np.int8)


def multiclass_y(sids, labels) -> np.ndarray:
    return np.asarray([int(labels[s]["c"]) for s in sids], dtype=np.int8)


def f1_scalar(y, pred) -> float:
    y = np.asarray(y).astype(int)
    pred = np.asarray(pred).astype(int)
    tp = int(np.sum((y == 1) & (pred == 1)))
    fp = int(np.sum((y == 0) & (pred == 1)))
    fn = int(np.sum((y == 1) & (pred == 0)))
    return prf_counts(tp, fp, fn)["f1"]


def best_threshold(y, scores) -> tuple[float, float]:
    """驗證集上 F1 最高的門檻。平手時取較接近 0.5 的門檻。"""
    y = np.asarray(y).astype(int)
    scores = np.asarray(scores, dtype=float)
    if len(scores) == 0:
        return 0.5, 0.0
    cands = np.unique(np.concatenate([scores, [0.5]]))
    best_t, best_f, best_dist = 0.5, -1.0, 1e9
    for t in cands:
        f = f1_scalar(y, scores >= t)
        dist = abs(float(t) - 0.5)
        if f > best_f + 1e-12 or (abs(f - best_f) <= 1e-12 and dist < best_dist - 1e-12):
            best_t, best_f, best_dist = float(t), f, dist
    return best_t, best_f


def binary_metrics(y, pred, scores) -> dict:
    y = np.asarray(y).astype(int)
    pred = np.asarray(pred).astype(int)
    scores = np.asarray(scores, dtype=float)
    tp = int(np.sum((y == 1) & (pred == 1)))
    fp = int(np.sum((y == 0) & (pred == 1)))
    fn = int(np.sum((y == 1) & (pred == 0)))
    tn = int(np.sum((y == 0) & (pred == 0)))
    pr = prf_counts(tp, fp, fn)
    pairs = list(zip(y.tolist(), pred.tolist()))
    out = {
        "n": int(len(y)),
        "P": pr["precision"],
        "R": pr["recall"],
        "F1": pr["f1"],
        "kappa": cohen_kappa(pairs, [0, 1]),
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }
    if len(np.unique(y)) > 1 and np.isfinite(scores).all():
        out["pr_auc"] = float(average_precision_score(y, scores))
    else:
        out["pr_auc"] = None
    return out


def f1_batch(y_rows, p_rows) -> np.ndarray:
    tp = np.sum((y_rows == 1) & (p_rows == 1), axis=1)
    fp = np.sum((y_rows == 0) & (p_rows == 1), axis=1)
    fn = np.sum((y_rows == 1) & (p_rows == 0), axis=1)
    prec = np.divide(tp, tp + fp, out=np.zeros(len(tp), dtype=float), where=(tp + fp) > 0)
    rec = np.divide(tp, tp + fn, out=np.zeros(len(tp), dtype=float), where=(tp + fn) > 0)
    return np.divide(2 * prec * rec, prec + rec, out=np.zeros(len(tp), dtype=float), where=(prec + rec) > 0)


def bootstrap_f1(y, pred, idx) -> dict:
    yb = np.asarray(y).astype(int)[idx]
    pb = np.asarray(pred).astype(int)[idx]
    scores = f1_batch(yb, pb)
    lo, hi = np.quantile(scores, [0.025, 0.975])
    return {"n": int(idx.shape[0]), "lo": float(lo), "hi": float(hi), "mean": float(scores.mean())}


def four_class_metrics(y, pred) -> dict:
    y = np.asarray(y).astype(int)
    pred = np.asarray(pred).astype(int)
    pairs = list(zip(y.tolist(), pred.tolist()))
    acc = float(np.mean(y == pred)) if len(y) else 0.0
    return {"n": int(len(y)), "accuracy": acc, "kappa": cohen_kappa(pairs, [0, 1, 2, 3])}


def positive_scores(clf, X) -> np.ndarray:
    if hasattr(clf, "predict_proba"):
        proba = clf.predict_proba(X)
        classes = [int(c) for c in clf.classes_]
        if 1 not in classes:
            return np.zeros(X.shape[0], dtype=float)
        return np.asarray(proba[:, classes.index(1)], dtype=float)
    if hasattr(clf, "decision_function"):
        return np.asarray(clf.decision_function(X), dtype=float).ravel()
    raise TypeError(type(clf))


def class_weight_for(balance: str):
    return "balanced" if balance == "b" else None


def make_binary(name: str, params: dict, balance: str):
    cw = class_weight_for(balance)
    if name == "logreg":
        return LogisticRegression(
            C=params["C"], solver="liblinear", max_iter=1000, class_weight=cw, random_state=SEED
        )
    if name == "linearsvc":
        return LinearSVC(
            C=params["C"], class_weight=cw, dual="auto", max_iter=4000, random_state=SEED
        )
    if name == "rbfsvc":
        return SVC(
            kernel="rbf", C=params["C"], gamma=params["gamma"], class_weight=cw, random_state=SEED, cache_size=500
        )
    if name == "dt_clf":
        return DecisionTreeClassifier(
            max_depth=params["max_depth"], min_samples_leaf=params["min_samples_leaf"],
            class_weight=cw, random_state=SEED,
        )
    if name == "rf":
        return RandomForestClassifier(
            n_estimators=params["n_estimators"], max_depth=params["max_depth"],
            min_samples_leaf=params["min_samples_leaf"], max_features="sqrt",
            class_weight=cw, random_state=SEED, n_jobs=-1,
        )
    if name == "hgb":
        return HistGradientBoostingClassifier(
            learning_rate=params["learning_rate"], max_depth=params["max_depth"],
            max_iter=params["max_iter"], min_samples_leaf=20, early_stopping=False,
            class_weight=cw, random_state=SEED,
        )
    if name == "knn":
        return KNeighborsClassifier(
            n_neighbors=params["n_neighbors"], weights=params["weights"],
            metric="cosine", algorithm="brute",
        )
    raise KeyError(name)


def make_multiclass(name: str, params: dict, balance: str):
    cw = class_weight_for(balance)
    if name == "logreg":
        return LogisticRegression(
            C=params["C"], solver="saga", max_iter=500, tol=1e-3, class_weight=cw, random_state=SEED
        )
    if name == "linearsvc":
        return LinearSVC(
            C=params["C"], class_weight=cw, dual="auto", max_iter=4000, random_state=SEED
        )
    if name == "rbfsvc":
        return SVC(
            kernel="rbf", C=params["C"], gamma=params["gamma"], class_weight=cw, random_state=SEED, cache_size=500
        )
    if name == "dt_clf":
        return DecisionTreeClassifier(
            max_depth=params["max_depth"], min_samples_leaf=params["min_samples_leaf"],
            class_weight=cw, random_state=SEED,
        )
    if name == "rf":
        return RandomForestClassifier(
            n_estimators=params["n_estimators"], max_depth=params["max_depth"],
            min_samples_leaf=params["min_samples_leaf"], max_features="sqrt",
            class_weight=cw, random_state=SEED, n_jobs=-1,
        )
    if name == "hgb":
        return HistGradientBoostingClassifier(
            learning_rate=params["learning_rate"], max_depth=params["max_depth"],
            max_iter=params["max_iter"], min_samples_leaf=20, early_stopping=False,
            class_weight=cw, random_state=SEED,
        )
    if name == "knn":
        return KNeighborsClassifier(
            n_neighbors=params["n_neighbors"], weights=params["weights"],
            metric="cosine", algorithm="brute",
        )
    return None


def grids(name: str) -> list[dict]:
    if name == "logreg":
        return [{"C": c} for c in (0.1, 0.3, 1.0, 3.0, 10.0)]
    if name == "linearsvc":
        return [{"C": c} for c in (0.1, 0.3, 1.0, 3.0, 10.0)]
    if name == "rbfsvc":
        return [
            {"C": 1.0, "gamma": "scale"},
            {"C": 3.0, "gamma": "scale"},
            {"C": 10.0, "gamma": "scale"},
            {"C": 1.0, "gamma": 0.01},
            {"C": 3.0, "gamma": 0.01},
        ]
    if name in ("dt_clf", "dt_reg"):
        return [
            {"max_depth": d, "min_samples_leaf": m}
            for d, m in ((8, 5), (16, 5), (32, 2), (32, 10), (None, 5), (None, 20))
        ]
    if name == "rf":
        return [
            {"n_estimators": n, "max_depth": d, "min_samples_leaf": m}
            for n, d, m in ((100, 16, 5), (200, 24, 2), (200, None, 5), (300, 32, 2))
        ]
    if name == "hgb":
        return [
            {"learning_rate": lr, "max_depth": d, "max_iter": it}
            for lr, d, it in ((0.1, 3, 200), (0.1, 6, 200), (0.05, 6, 300), (0.2, 4, 150))
        ]
    if name == "knn":
        return [
            {"n_neighbors": k, "weights": w}
            for k, w in ((5, "uniform"), (11, "uniform"), (21, "uniform"), (41, "uniform"), (11, "distance"), (21, "distance"))
        ]
    return []


def phrases_sorted(phrases: list[str]) -> list[str]:
    return sorted(set(phrases), key=len, reverse=True)


AFTERSALES_S = phrases_sorted(AFTERSALES)
CHURN_S = phrases_sorted(CHURN)
LEFT_S = phrases_sorted(LEFT)
COMPLAINT_S = phrases_sorted(COMPLAINT)


def count_phrases(text: str, phrases: list[str]) -> int:
    if not text:
        return 0
    n = 0
    i = 0
    while i < len(text):
        hit = None
        for p in phrases:
            if text.startswith(p, i):
                hit = p
                break
        if hit:
            n += 1
            i += len(hit)
        else:
            i += 1
    return n


def keyword_score(text: str, variant: str) -> float:
    churn_n = count_phrases(text, CHURN_S)
    after_n = count_phrases(text, AFTERSALES_S)
    if variant == "strict":
        return 1.0 if churn_n and after_n else 0.0
    if variant == "churn_only":
        return 1.0 if churn_n else 0.0
    if churn_n >= 2 and after_n:
        return 0.95
    if churn_n >= 1 and after_n:
        return 0.75
    if churn_n >= 1:
        return 0.40
    if after_n:
        return 0.15
    return 0.0


def keyword_class(text: str) -> int:
    if count_phrases(text, LEFT_S):
        return 3
    if count_phrases(text, CHURN_S):
        return 2
    if count_phrases(text, COMPLAINT_S) and count_phrases(text, AFTERSALES_S):
        return 1
    return 0


def text_of(ctx_row: dict | None, kind: str) -> str:
    row = ctx_row or {}
    title = row.get("title") or ""
    prev = " ".join(row.get("prev") or [])
    target = (row.get("text") or "").strip()
    nxt = row.get("next") or ""
    if kind == "target":
        return target or "。"
    if kind == "context":
        return "\n".join(x for x in (title, prev, nxt) if x) or "。"
    return "\n".join(x for x in (title, prev, target, nxt) if x) or "。"


def vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        analyzer="char",
        ngram_range=(1, 3),
        min_df=2,
        max_features=MAX_FEATURES,
        sublinear_tf=True,
        lowercase=False,
        dtype=np.float32,
    )


class MatrixBundle:
    def __init__(self, feature: str, balance: str):
        self.feature = feature
        self.balance = balance
        self.vec_t = None
        self.vec_c = None
        self.svd = None
        self.X_train = None
        self.X_val = None
        self.X_test = None
        self.X_human = None
        self.Z_train = None
        self.Z_val = None
        self.Z_test = None
        self.Z_human = None
        self.n_features = 0
        self.svd_var = None
        self.y_train = None
        self.y_train_c = None
        self.y_val = None
        self.y_val_c = None
        self.y_test = None
        self.y_test_c = None
        self.sw = None
        self.n_train_rows = 0
        self.n_train_unique = 0


def fit_matrices(feature, balance, train_sids, val_sids, test_sids, human_sids, ctx, labels) -> MatrixBundle:
    from scipy import sparse

    b = MatrixBundle(feature, balance)
    unique = list(dict.fromkeys(train_sids))
    b.n_train_rows = len(train_sids)
    b.n_train_unique = len(unique)
    b.vec_t = vectorizer()
    Xt_u = b.vec_t.fit_transform([text_of(ctx.get(s), "target") for s in unique])
    parts = [Xt_u]
    if feature == "f2":
        b.vec_c = vectorizer()
        parts.append(b.vec_c.fit_transform([text_of(ctx.get(s), "context") for s in unique]))
    Xu = sparse.hstack(parts, format="csr")
    b.n_features = int(Xu.shape[1])
    index = {sid: i for i, sid in enumerate(unique)}
    rows = np.asarray([index[s] for s in train_sids], dtype=np.int32)
    b.X_train = Xu[rows]
    b.X_val = transform_sids(b, val_sids, ctx)
    b.X_test = transform_sids(b, test_sids, ctx)
    b.X_human = transform_sids(b, human_sids, ctx)
    b._Xu = Xu
    b._index = index
    b.y_train = binary_y(train_sids, labels)
    b.y_train_c = multiclass_y(train_sids, labels)
    b.y_val = binary_y(val_sids, labels)
    b.y_val_c = multiclass_y(val_sids, labels)
    b.y_test = binary_y(test_sids, labels)
    b.y_test_c = multiclass_y(test_sids, labels)
    if balance == "b":
        b.sw = compute_sample_weight("balanced", b.y_train)
    return b


def transform_sids(b: MatrixBundle, sids, ctx):
    from scipy import sparse

    Xt = b.vec_t.transform([text_of(ctx.get(s), "target") for s in sids])
    if b.feature == "f1":
        return Xt
    Xc = b.vec_c.transform([text_of(ctx.get(s), "context") for s in sids])
    return sparse.hstack([Xt, Xc], format="csr")


def ensure_svd(b: MatrixBundle) -> None:
    if b.svd is not None:
        return
    n_comp = min(SVD_DIM, b._Xu.shape[0] - 1, b._Xu.shape[1] - 1)
    b.svd = TruncatedSVD(n_components=n_comp, random_state=SEED)
    log(f"  SVD {b.feature}/{b.balance} -> {n_comp}")
    Zu = b.svd.fit_transform(b._Xu)
    b.svd_var = float(b.svd.explained_variance_ratio_.sum())
    b._Zu = Zu
    b.Z_val = b.svd.transform(b.X_val)
    b.Z_test = b.svd.transform(b.X_test)
    b.Z_human = b.svd.transform(b.X_human)


def dense_train(b: MatrixBundle, train_sids) -> np.ndarray:
    ensure_svd(b)
    rows = np.asarray([b._index[s] for s in train_sids], dtype=np.int32)
    return b._Zu[rows]


def fit_timed(clf, X, y, sample_weight=None):
    t0 = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if sample_weight is None:
            clf.fit(X, y)
        else:
            clf.fit(X, y, sample_weight=sample_weight)
    msgs = [str(w.message) for w in caught]
    return clf, time.perf_counter() - t0, msgs


def jsonable_params(params: dict) -> dict:
    out = {}
    for k, v in params.items():
        out[k] = None if v is None else v
    return out


def select_sklearn(name, params_list, b: MatrixBundle, train_sids):
    if name in DENSE_MODELS:
        X_train = dense_train(b, train_sids)
        X_val = b.Z_val
    else:
        X_train = b.X_train
        X_val = b.X_val
    trials = []
    best = None
    sw = b.sw if name == "dt_reg" else None
    for params in params_list:
        t0 = time.perf_counter()
        if name == "dt_reg":
            clf = DecisionTreeRegressor(
                max_depth=params["max_depth"], min_samples_leaf=params["min_samples_leaf"], random_state=SEED
            )
            clf, _, msgs = fit_timed(clf, X_train, b.y_train_c, sw)
            val_scores = np.asarray(clf.predict(X_val), dtype=float) / 3.0
        else:
            clf = make_binary(name, params, b.balance)
            clf, _, msgs = fit_timed(clf, X_train, b.y_train, None)
            val_scores = positive_scores(clf, X_val)
        thr, f_best = best_threshold(b.y_val, val_scores)
        f05 = f1_scalar(b.y_val, val_scores >= 0.5)
        ap = None
        if len(np.unique(b.y_val)) > 1 and np.isfinite(val_scores).all():
            ap = float(average_precision_score(b.y_val, val_scores))
        row = {
            "params": jsonable_params(params),
            "val_F1_best": f_best,
            "val_threshold": thr,
            "val_F1_0.5": f05,
            "val_pr_auc": ap,
            "seconds": time.perf_counter() - t0,
            "warnings": msgs[:5],
        }
        trials.append(row)
        better = best is None or f_best > best["val_F1_best"] + 1e-12
        if not better and best is not None and abs(f_best - best["val_F1_best"]) <= 1e-12:
            better = (ap or -1) > (best["val_pr_auc"] or -1) + 1e-12
        if better:
            best = row
        log(f"    {name} {params} valF1={f_best:.3f} thr={thr:.3f} F1@0.5={f05:.3f}")
    return best, trials


def bundle_bytes(obj) -> int:
    import joblib
    import tempfile

    fd, path = tempfile.mkstemp(suffix=".joblib")
    os.close(fd)
    try:
        joblib.dump(obj, path, compress=0)
        return int(Path(path).stat().st_size)
    finally:
        Path(path).unlink(missing_ok=True)


def predict_four(name, params, b: MatrixBundle, train_sids, X_test):
    """四類補充。超參沿用二元驗證集選出的那組，不再重選。"""
    if name == "dt_reg":
        clf = DecisionTreeRegressor(
            max_depth=params["max_depth"], min_samples_leaf=params["min_samples_leaf"], random_state=SEED
        )
        sw = b.sw if b.balance == "b" else None
        X_train = b.X_train
        clf, sec, _ = fit_timed(clf, X_train, b.y_train_c, sw)
        pred = np.clip(np.rint(clf.predict(X_test)), 0, 3).astype(int)
        return pred, sec, "回歸預測值四捨五入到 0–3"
    if name == "knn" and b.balance == "b":
        note = "KNN 沒有 class_weight，設定 b 是未加權的全訓練池"
    else:
        note = "四類模型使用同一組超參；設定 b 的 class_weight=balanced 作用在 c=0–3"
    clf = make_multiclass(name, params, b.balance)
    if clf is None:
        return None, 0.0, "這個模型沒有四類分類器"
    if name in DENSE_MODELS:
        X_train = dense_train(b, train_sids)
    else:
        X_train = b.X_train
    clf, sec, _ = fit_timed(clf, X_train, b.y_train_c, None)
    pred = np.asarray(clf.predict(X_test), dtype=int)
    return pred, sec, note


def finalize_sklearn(name, best_params, b: MatrixBundle, train_sids):
    params = best_params
    use_dense = name in DENSE_MODELS
    X_train = dense_train(b, train_sids) if use_dense else b.X_train
    X_val = b.Z_val if use_dense else b.X_val
    X_test = b.Z_test if use_dense else b.X_test
    X_human = b.Z_human if use_dense else b.X_human
    notes = []
    if name == "knn":
        notes.append("KNN 用 TF-IDF 的餘弦距離，不經 SVD。設定 b 無法套用 class_weight，因此是未加權全訓練池。")
    if name == "dt_reg" and b.balance == "b":
        notes.append("決策樹回歸沒有 class_weight。設定 b 對二元標籤使用 balanced sample_weight。")
    if name in ("linearsvc", "rbfsvc"):
        base = make_binary(name, params, b.balance)
        clf = CalibratedClassifierCV(estimator=base, method="sigmoid", cv=3)
        notes.append("線性／RBF SVM 的 C（與 gamma）依驗證集最佳 F1 選定；機率用訓練集內部 3 折 sigmoid 校準，0.5 與 PR-AUC 都用校準後的機率。驗證集只用來選門檻，沒有參與校準。")
        clf, train_s, msgs = fit_timed(clf, X_train, b.y_train, None)
        val_scores = positive_scores(clf, X_val)
    elif name == "dt_reg":
        clf = DecisionTreeRegressor(
            max_depth=params["max_depth"], min_samples_leaf=params["min_samples_leaf"], random_state=SEED
        )
        sw = b.sw if b.balance == "b" else None
        clf, train_s, msgs = fit_timed(clf, X_train, b.y_train_c, sw)
        val_scores = np.asarray(clf.predict(X_val), dtype=float) / 3.0
        notes.append("二元分數是預測的 c／3，所以門檻 0.5 等於預測值 1.5。")
    else:
        clf = make_binary(name, params, b.balance)
        clf, train_s, msgs = fit_timed(clf, X_train, b.y_train, None)
        val_scores = positive_scores(clf, X_val)
    thr, val_f = best_threshold(b.y_val, val_scores)
    if name == "dt_reg":
        test_scores = np.asarray(clf.predict(X_test), dtype=float) / 3.0
        human_scores = np.asarray(clf.predict(X_human), dtype=float) / 3.0
    else:
        test_scores = positive_scores(clf, X_test)
        human_scores = positive_scores(clf, X_human)
    # 推論時間：最終模型對測試集預測，重複 3 次取平均。不含向量化。
    t0 = time.perf_counter()
    repeats = 3
    for _ in range(repeats):
        if name == "dt_reg":
            clf.predict(X_test)
        else:
            positive_scores(clf, X_test)
    infer_s = (time.perf_counter() - t0) / repeats / max(len(b.y_test), 1)
    pred_best = (test_scores >= thr).astype(np.int8)
    pred_05 = (test_scores >= 0.5).astype(np.int8)
    human_pred = (human_scores >= thr).astype(np.int8)
    four_pred, four_s, four_note = (None, 0.0, "")
    if name != "dt_reg":
        four_pred, four_s, four_note = predict_four(name, params, b, train_sids, X_test)
    else:
        four_pred = np.clip(np.rint(test_scores * 3.0), 0, 3).astype(int)
        four_s = 0.0
        four_note = "四類與二元共用同一棵回歸樹，不另計訓練時間。"
    piece = {"clf": clf}
    if use_dense and b.svd is not None:
        piece["svd"] = b.svd
    piece["vec_t"] = b.vec_t
    if b.vec_c is not None:
        piece["vec_c"] = b.vec_c
    return {
        "clf_notes": notes,
        "train_seconds": train_s,
        "infer_seconds_per_sentence": infer_s,
        "model_bytes": bundle_bytes(piece),
        "estimator_bytes": bundle_bytes(clf),
        "val_threshold": thr,
        "val_F1_at_threshold": val_f,
        "val_metrics_best": binary_metrics(b.y_val, val_scores >= thr, val_scores),
        "val_metrics_0.5": binary_metrics(b.y_val, val_scores >= 0.5, val_scores),
        "test_scores": test_scores,
        "test_pred_best": pred_best,
        "test_pred_0.5": pred_05,
        "human_pred": human_pred,
        "human_scores": human_scores,
        "fit_warnings": msgs[:8],
        "four_pred": four_pred,
        "four_train_seconds": four_s,
        "four_note": four_note,
        "four_metrics": four_class_metrics(b.y_test_c, four_pred) if four_pred is not None else None,
    }


def run_keyword(feature, b_unused_sids, ctx, val_sids, test_sids, human_sids, labels):
    kind = "target" if feature == "f1" else "window"

    def scores(sids, variant):
        return np.asarray([keyword_score(text_of(ctx.get(s), kind), variant) for s in sids], dtype=float)

    y_val = binary_y(val_sids, labels)
    y_test = binary_y(test_sids, labels)
    y_test_c = multiclass_y(test_sids, labels)
    trials = []
    best = None
    best_variant = None
    for variant in ("strict", "churn_only", "graded"):
        val_scores = scores(val_sids, variant)
        thr, f_best = best_threshold(y_val, val_scores)
        f05 = f1_scalar(y_val, val_scores >= 0.5)
        ap = float(average_precision_score(y_val, val_scores)) if len(np.unique(y_val)) > 1 else None
        row = {
            "params": {"variant": variant},
            "val_F1_best": f_best,
            "val_threshold": thr,
            "val_F1_0.5": f05,
            "val_pr_auc": ap,
            "seconds": 0.0,
            "warnings": [],
        }
        trials.append(row)
        if best is None or f_best > best["val_F1_best"] + 1e-12:
            best = row
            best_variant = variant
        log(f"    keyword {feature} {variant} valF1={f_best:.3f} thr={thr:.3f}")
    t0 = time.perf_counter()
    test_scores = scores(test_sids, best_variant)
    human_scores = scores(human_sids, best_variant)
    train_s = time.perf_counter() - t0
    thr = best["val_threshold"]
    # 關鍵詞沒有訓練；上面的時間是測試集規則比對。推論時間另計。
    texts = [text_of(ctx.get(s), kind) for s in test_sids]
    t0 = time.perf_counter()
    for _ in range(3):
        for text in texts:
            keyword_score(text, best_variant)
    infer_s = (time.perf_counter() - t0) / 3 / max(len(test_sids), 1)
    pred_best = (test_scores >= thr).astype(np.int8)
    pred_05 = (test_scores >= 0.5).astype(np.int8)
    four_pred = np.asarray([keyword_class(text_of(ctx.get(s), kind)) for s in test_sids], dtype=int)
    lexicon_bytes = len(json.dumps({
        "aftersales": AFTERSALES, "churn": CHURN, "left": LEFT, "complaint": COMPLAINT
    }, ensure_ascii=False).encode("utf-8"))
    return {
        "params": {"variant": best_variant},
        "trials": trials,
        "search_seconds": 0.0,
        "train_seconds": 0.0,
        "rule_apply_seconds_test": train_s,
        "infer_seconds_per_sentence": infer_s,
        "model_bytes": lexicon_bytes,
        "estimator_bytes": lexicon_bytes,
        "val_threshold": thr,
        "val_metrics_best": binary_metrics(y_val, scores(val_sids, best_variant) >= thr, scores(val_sids, best_variant)),
        "val_metrics_0.5": binary_metrics(y_val, scores(val_sids, best_variant) >= 0.5, scores(val_sids, best_variant)),
        "test_scores": test_scores,
        "test_pred_best": pred_best,
        "test_pred_0.5": pred_05,
        "human_pred": (human_scores >= thr).astype(np.int8),
        "y_test": y_test,
        "four_metrics": four_class_metrics(y_test_c, four_pred),
        "four_train_seconds": 0.0,
        "four_note": "四類是固定規則：已離開詞→3、其餘流失詞→2、售後抱怨詞→1，否則 0。沒有在驗證集上重選這組對應。",
        "notes": [
            "關鍵詞沒有訓練，不平衡設定 a／b 結果相同，只算一次。",
            "f1 只看目標句；f2 看標題＋前 2 句＋目標句＋後 1 句。",
            f"選定變體 {best_variant}。strict＝流失詞與售後詞都要出現；churn_only＝只要流失詞；graded＝依命中數給 0.15–0.95 分。",
        ],
        "fit_warnings": [],
    }


def mcnemar_exact(y, pred, r4_pred) -> dict:
    from scipy.stats import binomtest

    y = np.asarray(y).astype(int)
    pred = np.asarray(pred).astype(int)
    r4_pred = np.asarray(r4_pred).astype(int)
    model_ok = pred == y
    r4_ok = r4_pred == y
    b = int(np.sum(~model_ok & r4_ok))
    c = int(np.sum(model_ok & ~r4_ok))
    n_disc = b + c
    if n_disc == 0:
        p = 1.0
    else:
        p = float(binomtest(b, n_disc, 0.5, alternative="two-sided").pvalue)
    return {"model_wrong_r4_right": b, "model_right_r4_wrong": c, "n_discordant": n_disc, "p_exact": p}


def human_block(human_rows, pred_by_sid) -> dict:
    out = {}
    groups = {
        "random": [r for r in human_rows if r["stratum"] == "A_random"],
        "hard": [r for r in human_rows if r["stratum"] == "B_hard"],
        "all": human_rows,
    }
    for name, rows in groups.items():
        usable = [r for r in rows if r["sid"] in pred_by_sid and r["churn"] is not None]
        if not usable:
            out[name] = None
            continue
        y = np.asarray([r["churn"] for r in usable], dtype=int)
        pred = np.asarray([pred_by_sid[r["sid"]] for r in usable], dtype=int)
        scores = pred.astype(float)
        m = binary_metrics(y, pred, scores)
        m["n_pos"] = int(y.sum())
        m["pr_auc"] = None
        out[name] = m
    return out


def load_human():
    from openpyxl import load_workbook

    src = P / "human_labels_arbitration_v2.xlsx"
    if not src.exists():
        src = P / "human_labels_arbitration.xlsx"
    ws = load_workbook(src, data_only=True)["仲裁"]
    hdr = [c.value for c in ws[1]]
    i_sid, i_c = hdr.index("sid"), hdr.index("最終流失(是/否)")
    final = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r or not r[i_sid]:
            continue
        v = (str(r[i_c]) if r[i_c] is not None else "").strip()
        if v in ("是", "1", "Y", "y", "true", "True"):
            churn = 1
        elif v in ("否", "0", "N", "n", "false", "False"):
            churn = 0
        else:
            continue
        final[str(r[i_sid])] = churn
    manifest = {m["sid"]: m for m in load_jsonl(P / "human_label_manifest.jsonl")}
    rows = []
    for sid, churn in final.items():
        m = manifest.get(sid, {})
        rows.append({
            "sid": sid,
            "churn": churn,
            "stratum": m.get("stratum"),
            "set": m.get("set"),
            "r4_c": m.get("r4_c"),
            "haiku_c": m.get("haiku_c"),
        })
    return src.name, rows


def reference_metrics(split, human_rows) -> dict:
    labels = split["labels"]
    test_sids = split["test_sids"]
    y = binary_y(test_sids, labels)
    y_c = multiclass_y(test_sids, labels)
    r4_rows = {r["sid"]: r for r in load_jsonl(P / "jev_lora_r4_ep2_pilot.jsonl")}
    hk_rows = {r["sid"]: r for r in load_jsonl(P / "churn_labels.jsonl")}
    r4_c = np.asarray([int(r4_rows[s]["c_expect"]) for s in test_sids], dtype=int)
    r4_pred = (r4_c >= 2).astype(np.int8)
    r4_p = []
    for s in test_sids:
        p = r4_rows[s]["churn_p"]
        if isinstance(p, dict):
            r4_p.append(float(p.get("2", 0)) + float(p.get("3", 0)))
        else:
            r4_p.append(float(p[2]) + float(p[3]))
    r4_scores = np.asarray(r4_p, dtype=float)
    hk_c = np.asarray([int(hk_rows[s]["c"]) for s in test_sids], dtype=int)
    hk_pred = (hk_c >= 2).astype(np.int8)
    # Haiku 檔只有等級、沒有機率。PR-AUC 不計算。
    hk_metrics = binary_metrics(y, hk_pred, hk_pred.astype(float))
    hk_metrics["pr_auc"] = None
    out = {
        "r4": {
            "source": "jev_lora_r4_ep2_pilot.jsonl c_expect；PR-AUC 用 churn_p 的 P(c=2)+P(c=3)",
            "metrics": binary_metrics(y, r4_pred, r4_scores),
            "four": four_class_metrics(y_c, r4_c),
            "pred": r4_pred,
            "cited_T8": {"P": 0.617, "R": 0.769, "F1": 0.685, "kappa": 0.642},
            "train_seconds_T8": 17934,
            "infer_seconds_per_sentence_T8": 0.69,
        },
        "haiku": {
            "source": "churn_labels.jsonl 的 c；測試集 600 句都有標籤",
            "metrics": hk_metrics,
            "four": four_class_metrics(y_c, hk_c),
            "pred": hk_pred,
            "cited_T8": {"P": 0.60, "R": 0.55, "F1": 0.58, "kappa": 0.53},
        },
    }
    # 人工金標上的 r4／Haiku，用 manifest 的 r4_c、haiku_c，與 T9 同一來源。
    def from_manifest(key):
        pred = {}
        for row in human_rows:
            val = row.get(key)
            if val is None:
                continue
            pred[row["sid"]] = int(int(val) >= 2)
        return human_block(human_rows, pred)

    out["r4"]["human"] = from_manifest("r4_c")
    out["haiku"]["human"] = from_manifest("haiku_c")
    return out


def pack_run(meta, payload, y_test, boot_idx, r4_pred) -> dict:
    pred = payload["test_pred_best"]
    pred05 = payload["test_pred_0.5"]
    scores = payload["test_scores"]
    test_best = binary_metrics(y_test, pred, scores)
    test_05 = binary_metrics(y_test, pred05, scores)
    ci = bootstrap_f1(y_test, pred, boot_idx)
    ci05 = bootstrap_f1(y_test, pred05, boot_idx)
    boot_model = f1_batch(np.asarray(y_test).astype(int)[boot_idx], np.asarray(pred).astype(int)[boot_idx])
    boot_r4 = f1_batch(np.asarray(y_test).astype(int)[boot_idx], np.asarray(r4_pred).astype(int)[boot_idx])
    delta = boot_model - boot_r4
    dlo, dhi = np.quantile(delta, [0.025, 0.975])
    packed = {
        **meta,
        "val_threshold": payload["val_threshold"],
        "val_metrics_best": payload["val_metrics_best"],
        "val_metrics_0.5": payload["val_metrics_0.5"],
        "test_best": test_best,
        "test_0.5": test_05,
        "f1_ci95_best": ci,
        "f1_ci95_0.5": ci05,
        "paired_f1_delta_vs_r4": {
            "mean": float(delta.mean()),
            "lo": float(dlo),
            "hi": float(dhi),
            "excludes_zero": bool(dlo > 0 or dhi < 0),
        },
        "mcnemar_vs_r4": mcnemar_exact(y_test, pred, r4_pred),
        "train_seconds": payload["train_seconds"],
        "infer_seconds_per_sentence": payload["infer_seconds_per_sentence"],
        "model_bytes": payload["model_bytes"],
        "estimator_bytes": payload["estimator_bytes"],
        "four_class": payload.get("four_metrics"),
        "four_train_seconds": payload.get("four_train_seconds"),
        "four_note": payload.get("four_note"),
        "notes": payload.get("notes") or payload.get("clf_notes") or [],
        "fit_warnings": payload.get("fit_warnings") or [],
        "human": payload.get("human"),
        "test_pred_best": np.asarray(pred).astype(int).tolist(),
        "test_pred_0.5": np.asarray(pred05).astype(int).tolist(),
    }
    return packed


def save_out(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # 預測向量留在檔內，方便事後核對；這個檔在 data/ 底下，不進 repo。
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--models", default=",".join(MODEL_NAMES))
    ap.add_argument("--features", default="f1,f2")
    ap.add_argument("--balances", default="a,b")
    ap.add_argument("--bootstrap", type=int, default=N_BOOT)
    ap.add_argument("--out", default=str(P / "baseline_ml_results.json"))
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    if args.seed != SEED:
        raise SystemExit("本實驗固定 seed 42，與 r4 相同。")
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    features = [m.strip() for m in args.features.split(",") if m.strip()]
    balances = [m.strip() for m in args.balances.split(",") if m.strip()]
    unknown = [m for m in models if m not in MODEL_NAMES]
    if unknown:
        raise SystemExit(f"未知模型 {unknown}；可選 {MODEL_NAMES}")

    log("切分（make_split seed 42）")
    split = make_split(SEED)
    labels = split["labels"]
    sampled = oversample_pos_fraction(subsample_neg_multiple(split["train_sids"], labels, 3, SEED), labels, 0.40, SEED)
    check = check_split(split, sampled)
    log(json.dumps({k: check[k] for k in ("train", "val", "test", "sampled_c", "sampled_pos", "sampled_neg", "ok")}, ensure_ascii=False))
    if not check["ok"]:
        log("切分與 T8 不一致，停止。")
        for p in check["problems"]:
            log("  " + p)
        raise SystemExit(2)

    out_path = Path(args.out)
    doc = {
        "seed": SEED,
        "sklearn": __import__("sklearn").__version__,
        "numpy": np.__version__,
        "cpu_count": os.cpu_count(),
        "feature_note": {
            "analyzer": "char",
            "ngram_range": [1, 3],
            "min_df": 2,
            "max_features": MAX_FEATURES,
            "lowercase": False,
            "why_char": "中文句子沒有空白分詞。char_wb 依空白切詞，在這批句子上幾乎整句當成一個詞，邊界記號沒有分詞意義，所以用 char。",
            "f1": "目標句的字元 1–3 gram TF-IDF",
            "f2": "目標句 TF-IDF 與前後文（標題、前 2 句、後 1 句，不含目標句）TF-IDF 水平串接",
            "svd": "RBF SVM 與 HistGradientBoosting 使用 TruncatedSVD 300 維，只在該設定的訓練句上 fit。KNN 維持稀疏餘弦距離，不降維。",
            "vectorizer_fit": "每個特徵×不平衡設定各自在該設定的訓練句（設定 a 為抽樣後的不重複句）上 fit，驗證集與測試集只 transform。",
        },
        "split_check": check,
        "runs": [],
    }
    done = set()
    if args.resume and out_path.exists():
        prev = json.loads(out_path.read_text(encoding="utf-8"))
        doc["runs"] = prev.get("runs", [])
        done = {(r["model"], r["feature"], r["balance"]) for r in doc["runs"]}
        if "reference" in prev:
            doc["reference"] = prev["reference"]
        log(f"續跑，已有 {len(done)} 組")

    log("讀人工金標與對照預測")
    human_file, human_rows = load_human()
    ref = reference_metrics(split, human_rows)
    sets = {}
    for row in human_rows:
        sets[row["set"]] = sets.get(row["set"], 0) + 1
    train_set = set(split["train_sids"])
    val_set = set(split["val_sids"])
    test_set = set(split["test_sids"])
    overlap = {"train": 0, "val": 0, "test": 0, "outside": 0}
    for row in human_rows:
        if row["sid"] in test_set:
            overlap["test"] += 1
        elif row["sid"] in val_set:
            overlap["val"] += 1
        elif row["sid"] in train_set:
            overlap["train"] += 1
        else:
            overlap["outside"] += 1
    doc["human_gold"] = {
        "file": human_file,
        "n": len(human_rows),
        "n_pos": int(sum(r["churn"] for r in human_rows)),
        "by_set_manifest": sets,
        "overlap_with_r4_split": overlap,
        "by_stratum": {
            "A_random": int(sum(1 for r in human_rows if r["stratum"] == "A_random")),
            "B_hard": int(sum(1 for r in human_rows if r["stratum"] == "B_hard")),
            "A_random_pos": int(sum(r["churn"] for r in human_rows if r["stratum"] == "A_random")),
            "B_hard_pos": int(sum(r["churn"] for r in human_rows if r["stratum"] == "B_hard")),
        },
        "stratum_by_split": {
            stratum: {
                part: int(sum(1 for r in human_rows if r["stratum"] == stratum and (
                    (part == "test" and r["sid"] in test_set)
                    or (part == "val" and r["sid"] in val_set)
                    or (part == "train" and r["sid"] in train_set)
                )))
                for part in ("train", "val", "test")
            }
            for stratum in ("A_random", "B_hard")
        },
        "limitation": "隨機層正例 9 句，區間會很寬。這 300 句都不在訓練池：165 句在驗證集、135 句在測試集。驗證集那 165 句的文字與 Sonnet 標籤參與了超參和門檻選擇，所以它們的人工金標不是完全留出；測試集那 135 句沒有參與選擇。",
    }
    log(f"人工金標 {human_file} n={len(human_rows)} by_set={sets} pos={doc['human_gold']['by_stratum']}")

    need = split["train_sids"] + split["val_sids"] + split["test_sids"] + [r["sid"] for r in human_rows]
    log(f"建立前後文，句數 {len(set(need))}")
    ctx = build_context(need)
    missing_ctx = [s for s in need if s not in ctx]
    doc["missing_context"] = len(set(missing_ctx))
    log(f"缺前後文 {doc['missing_context']}")

    y_test = binary_y(split["test_sids"], labels)
    boot_idx = np.random.default_rng(SEED).integers(0, len(y_test), size=(args.bootstrap, len(y_test)))
    r4_pred = ref["r4"]["pred"]
    ref["r4"]["f1_ci95"] = bootstrap_f1(y_test, r4_pred, boot_idx)
    ref["haiku"]["f1_ci95"] = bootstrap_f1(y_test, ref["haiku"]["pred"], boot_idx)
    doc["reference"] = {
        "r4": {k: v for k, v in ref["r4"].items() if k != "pred"},
        "haiku": {k: v for k, v in ref["haiku"].items() if k != "pred"},
        "bootstrap_same_indices": True,
        "bootstrap_n": args.bootstrap,
    }
    # 與 T8 公布值核對。差超過 0.01 就停，避免指標定義漂掉。
    r4m = ref["r4"]["metrics"]
    if abs(r4m["F1"] - 0.684931506849315) > 1e-9 or abs(r4m["P"] - 0.6172839506172839) > 1e-9:
        log(f"r4 重算與 T8 不一致：{r4m}")
        raise SystemExit(3)
    log(f"r4 重算 P={r4m['P']:.3f} R={r4m['R']:.3f} F1={r4m['F1']:.3f} κ={r4m['kappa']:.3f} PR-AUC={r4m['pr_auc']:.3f}")
    hkm = ref["haiku"]["metrics"]
    log(f"Haiku 重算 P={hkm['P']:.3f} R={hkm['R']:.3f} F1={hkm['F1']:.3f} κ={hkm['kappa']:.3f}")

    human_sids = [r["sid"] for r in human_rows]
    keyword_cache = {}

    for feature in features:
        for balance in balances:
            train_sids = sampled if balance == "a" else list(split["train_sids"])
            log(f"特徵 {feature} 設定 {balance} 訓練列 {len(train_sids)}")
            bundle = None
            if any(m != "keyword" for m in models):
                bundle = fit_matrices(feature, balance, train_sids, split["val_sids"], split["test_sids"], human_sids, ctx, labels)
                log(f"  TF-IDF 維度 {bundle.n_features}，不重複訓練句 {bundle.n_train_unique}")
            for name in models:
                key = (name, feature, balance)
                if key in done:
                    log(f"  跳過已完成 {key}")
                    continue
                if name == "keyword":
                    cache_key = feature
                    if cache_key not in keyword_cache:
                        keyword_cache[cache_key] = run_keyword(
                            feature, None, ctx, split["val_sids"], split["test_sids"], human_sids, labels
                        )
                    payload = dict(keyword_cache[cache_key])
                    payload["human"] = human_block(human_rows, {sid: int(p) for sid, p in zip(human_sids, payload["human_pred"])})
                    meta = {
                        "model": name,
                        "feature": feature,
                        "balance": balance,
                        "balance_note": "關鍵詞沒有訓練，a 與 b 數字相同",
                        "params": payload["params"],
                        "trials": payload["trials"],
                        "search_seconds": 0.0,
                        "n_features": None,
                        "svd_explained_variance": None,
                    }
                    packed = pack_run(meta, payload, payload["y_test"], boot_idx, r4_pred)
                else:
                    assert bundle is not None
                    t_search = time.perf_counter()
                    best, trials = select_sklearn(name, grids(name), bundle, train_sids)
                    search_s = time.perf_counter() - t_search
                    log(f"  選定 {name} {best['params']}，重訓並評測試集")
                    payload = finalize_sklearn(name, best["params"], bundle, train_sids)
                    payload["human"] = human_block(
                        human_rows, {sid: int(p) for sid, p in zip(human_sids, payload["human_pred"])}
                    )
                    meta = {
                        "model": name,
                        "feature": feature,
                        "balance": balance,
                        "balance_note": (
                            "全部 c≥2，負例 3 倍，正例重複抽樣到 1040 句次"
                            if balance == "a"
                            else "不抽樣；支援的分類器用 class_weight=balanced"
                        ),
                        "params": best["params"],
                        "trials": trials,
                        "search_seconds": search_s,
                        "n_features": bundle.n_features,
                        "svd_explained_variance": bundle.svd_var if name in DENSE_MODELS else None,
                    }
                    packed = pack_run(meta, payload, bundle.y_test, boot_idx, r4_pred)
                tb = packed["test_best"]
                ci = packed["f1_ci95_best"]
                log(
                    f"  測試 {name}/{feature}/{balance} F1={tb['F1']:.3f} "
                    f"P={tb['P']:.3f} R={tb['R']:.3f} κ={tb['kappa']:.3f} "
                    f"CI=[{ci['lo']:.3f},{ci['hi']:.3f}]"
                )
                doc["runs"].append(packed)
                done.add(key)
                save_out(out_path, doc)
            if bundle is not None:
                del bundle
    save_out(out_path, doc)
    log(f"寫入 {out_path}，共 {len(doc['runs'])} 組")


if __name__ == "__main__":
    main()
