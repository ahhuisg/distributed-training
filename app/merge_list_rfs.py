def combine_rfs(rfs):
    rf_a = rfs[0]
    for rf in rfs[1:]:
        rf_a.estimators_ += rf.estimators_
        rf_a.n_estimators = len(rf_a.estimators_)
    return rf_a