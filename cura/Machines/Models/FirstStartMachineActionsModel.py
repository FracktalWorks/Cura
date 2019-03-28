# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, Dict, Any

from PyQt5.QtCore import QObject, Qt, pyqtProperty, pyqtSignal, pyqtSlot

from UM.Qt.ListModel import ListModel


#
# This model holds all first-start machine actions for the currently active machine. It has 2 roles:
#   - title   : the title/name of the action
#   - content : the QObject of the QML content of the action
#   - action  : the MachineAction object itself
#
class FirstStartMachineActionsModel(ListModel):

    TitleRole = Qt.UserRole + 1
    ContentRole = Qt.UserRole + 2
    ActionRole = Qt.UserRole + 3

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self.addRoleName(self.TitleRole, "title")
        self.addRoleName(self.ContentRole, "content")
        self.addRoleName(self.ActionRole, "action")

        self._current_action_index = 0

        from cura.CuraApplication import CuraApplication
        self._application = CuraApplication.getInstance()

        self._application.initializationFinished.connect(self._initialize)

    def _initialize(self) -> None:
        self._application.getMachineManager().globalContainerChanged.connect(self._update)
        self._update()

    currentActionIndexChanged = pyqtSignal()
    allFinished = pyqtSignal()  # Emitted when all actions have been finished.

    @pyqtProperty(int, notify = currentActionIndexChanged)
    def currentActionIndex(self) -> int:
        return self._current_action_index

    @pyqtProperty("QVariantMap", notify = currentActionIndexChanged)
    def currentItem(self) -> Optional[Dict[str, Any]]:
        if self._current_action_index >= self.count:
            return dict()
        else:
            return self.getItem(self._current_action_index)

    @pyqtProperty(bool, notify = currentActionIndexChanged)
    def hasMoreActions(self) -> bool:
        return self._current_action_index < self.count - 1

    @pyqtSlot()
    def goToNextAction(self) -> None:
        # finish the current item
        if "action" in self.currentItem:
            self.currentItem["action"].setFinished()

        if not self.hasMoreActions:
            self.allFinished.emit()
            self.reset()
            return

        self._current_action_index += 1
        self.currentActionIndexChanged.emit()

    # Resets the current action index to 0 so the wizard panel can show actions from the beginning.
    @pyqtSlot()
    def reset(self) -> None:
        self._current_action_index = 0
        self.currentActionIndexChanged.emit()

        if self.count == 0:
            self.allFinished.emit()

    def _update(self) -> None:
        global_stack = self._application.getMachineManager().activeMachine
        if global_stack is None:
            self.setItems([])
            return

        definition_id = global_stack.definition.getId()
        first_start_actions = self._application.getMachineActionManager().getFirstStartActions(definition_id)

        item_list = []
        for item in first_start_actions:
            item_list.append({"title": item.label,
                              "content": item.displayItem,
                              "action": item,
                              })

        self.setItems(item_list)
        self.reset()


__all__ = ["FirstStartMachineActionsModel"]
