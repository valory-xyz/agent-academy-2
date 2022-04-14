# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
    FinishedPrepareTxRound,
    Keep3rJobAbciApp,
    PrepareTxRound,
)
from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.registration_abci.rounds import (
    AgentRegistrationAbciApp,
    FinishedRegistrationRound,
    RegistrationRound,
)
from packages.valory.skills.reset_pause_abci.rounds import (
    FinishedResetAndPauseErrorRound,
    FinishedResetAndPauseRound,
    ResetAndPauseRound,
    ResetPauseABCIApp,
)

from packages.valory.skills.safe_deployment_abci.rounds import (
    RandomnessSafeRound,
    FinishedSafeRound,
    SafeDeploymentAbciApp,
)

from packages.keep3r_co.skills.keep3r_abci.rounds import (
    CheckSafeExistenceRound,
    Event as CheckSafeExistenceEvent,
)

abci_app_transition_mapping: AbciAppTransitionMapping = {
    FinishedRegistrationRound: CheckSafeExistenceRound,
    CheckSafeExistenceRound: {
        CheckSafeExistenceEvent.DONE: FinishedSafeRound,  # To the last round of safe deployment abci
        CheckSafeExistenceEvent.NEGATIVE: RandomnessSafeRound,  # To the 1st round of safe deployment abci
        CheckSafeExistenceEvent.NONE: RegistrationRound,  # NOTE: unreachable, to the first round of agent registration abci
        CheckSafeExistenceEvent.CHECK_TIMEOUT: RegistrationRound,  # To the first round of agent registration abci
        CheckSafeExistenceEvent.NO_MAJORITY: RegistrationRound,  # To the first round of agent registration abci
    },
    FinishedSafeRound: PrepareTxRound,
    FinishedPrepareTxRound: ResetAndPauseRound,
    FinishedResetAndPauseRound: RegistrationRound,
    FinishedResetAndPauseErrorRound: RegistrationRound,
}

Keep3rAbciApp = chain(
    (
        AgentRegistrationAbciApp,
        SafeDeploymentAbciApp,
        Keep3rJobAbciApp,
        ResetPauseABCIApp,
    ),
    abci_app_transition_mapping,
)
