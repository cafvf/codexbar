from codexbar.application.redeem import RedeemProcessStatus
from codexbar.application.reset_projection import RedeemAttemptState


def test_redeem_process_status_covers_projection_recovery_states() -> None:
    assert RedeemProcessStatus.REQUESTED.value == RedeemAttemptState.REQUESTED.value
    assert (
        RedeemProcessStatus.OUTCOME_UNKNOWN.value
        == RedeemAttemptState.OUTCOME_UNKNOWN.value
    )
    assert RedeemProcessStatus.SUCCEEDED.value == RedeemAttemptState.SUCCEEDED.value
