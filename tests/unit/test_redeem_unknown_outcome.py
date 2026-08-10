from codexbar.application.redeem import RedeemProcessStatus


def test_outcome_unknown_is_not_success_or_rejection() -> None:
    assert RedeemProcessStatus.OUTCOME_UNKNOWN not in {
        RedeemProcessStatus.SUCCEEDED,
        RedeemProcessStatus.ALREADY_REDEEMED,
        RedeemProcessStatus.REJECTED,
    }
