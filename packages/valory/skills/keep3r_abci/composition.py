# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This module contains the price estimation ABCI application."""
from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.keep3r_job_abci.rounds import (
    FinalizeActivationRound,
    FinalizeApproveBondRound,
    FinalizeBondingRound,
    FinalizeWorkRound,
    Keep3rJobAbciApp,
    PathSelectionRound,
)
from packages.valory.skills.registration_abci.rounds import (
    AgentRegistrationAbciApp,
    FinishedRegistrationRound,
    RegistrationRound,
    RegistrationStartupRound,
)
from packages.valory.skills.reset_pause_abci.rounds import (
    FinishedResetAndPauseErrorRound,
    FinishedResetAndPauseRound,
    ResetAndPauseRound,
    ResetPauseAbciApp,
)
from packages.valory.skills.termination_abci.rounds import BackgroundRound
from packages.valory.skills.termination_abci.rounds import Event as TerminationEvent
from packages.valory.skills.termination_abci.rounds import TerminationAbciApp
from packages.valory.skills.transaction_settlement_abci.rounds import (
    FailedRound as FailedTransactionSubmissionRound,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    FinishedTransactionSubmissionRound,
    RandomnessTransactionSubmissionRound,
    TransactionSubmissionAbciApp,
)


abci_app_transition_mapping: AbciAppTransitionMapping = {
    FinishedRegistrationRound: PathSelectionRound,
    FinalizeApproveBondRound: RandomnessTransactionSubmissionRound,
    FinalizeBondingRound: RandomnessTransactionSubmissionRound,
    FinalizeActivationRound: RandomnessTransactionSubmissionRound,
    FinalizeWorkRound: RandomnessTransactionSubmissionRound,
    FinishedTransactionSubmissionRound: ResetAndPauseRound,
    FailedTransactionSubmissionRound: ResetAndPauseRound,
    FinishedResetAndPauseRound: RegistrationRound,
    FinishedResetAndPauseErrorRound: RegistrationStartupRound,
}

Keep3rAbciApp = chain(
    (
        AgentRegistrationAbciApp,
        Keep3rJobAbciApp,
        TransactionSubmissionAbciApp,
        ResetPauseAbciApp,
    ),
    abci_app_transition_mapping,
).add_termination(
    background_round_cls=BackgroundRound,
    termination_event=TerminationEvent.TERMINATE,
    termination_abci_app=TerminationAbciApp,
)
