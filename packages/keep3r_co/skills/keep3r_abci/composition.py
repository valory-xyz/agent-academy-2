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
from packages.keep3r_co.skills.keep3r_job.rounds import (
    FinalizeActivationRound,
    FinalizeBondingRound,
    FinalizeWorkRound,
    Keep3rJobAbciApp,
    PathSelectionRound,
)
from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.registration_abci.rounds import (
    AgentRegistrationAbciApp,
    FinishedRegistrationFFWRound,
    FinishedRegistrationRound,
    RegistrationRound,
    RegistrationStartupRound,
)
from packages.valory.skills.reset_pause_abci.rounds import (
    FinishedResetAndPauseErrorRound,
    FinishedResetAndPauseRound,
    ResetAndPauseRound,
    ResetPauseABCIApp,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    FinishedTransactionSubmissionRound,
    RandomnessTransactionSubmissionRound,
    TransactionSubmissionAbciApp,
)


abci_app_transition_mapping: AbciAppTransitionMapping = {
    FinishedRegistrationRound: PathSelectionRound,
    FinishedRegistrationFFWRound: PathSelectionRound,
    FinalizeBondingRound: RandomnessTransactionSubmissionRound,
    FinalizeActivationRound: RandomnessTransactionSubmissionRound,
    FinalizeWorkRound: RandomnessTransactionSubmissionRound,
    FinishedTransactionSubmissionRound: ResetAndPauseRound,
    FinishedResetAndPauseRound: RegistrationRound,
    FinishedResetAndPauseErrorRound: RegistrationStartupRound,
}

Keep3rAbciApp = chain(
    (
        AgentRegistrationAbciApp,
        Keep3rJobAbciApp,
        TransactionSubmissionAbciApp,
        ResetPauseABCIApp,
    ),
    abci_app_transition_mapping,
)
