import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager
import org.kde.plasma.workspace.dbus as DBus

PlasmoidItem {
    id: root

    preferredRepresentation: fullRepresentation
    toolTipMainText: ""
    toolTipSubText: ""

    function kwin(member, args) {
        DBus.SessionBus.asyncCall({service: "org.kde.KWin", path: "/KWin", iface: "org.kde.KWin", member: member, arguments: args ?? []});
    }

    TaskManager.VirtualDesktopInfo { id: desktops }
    TaskManager.ActivityInfo { id: activities }

    fullRepresentation: RowLayout {
        spacing: 0
        Layout.minimumWidth: implicitWidth
        Layout.maximumWidth: implicitWidth

        WheelHandler {
            onWheel: event => root.kwin(event.angleDelta.y < 0 ? "nextDesktop" : "previousDesktop")
        }

        Repeater {
            model: desktops.desktopIds

            MouseArea {
                id: cell

                required property var modelData
                required property int index
                readonly property bool current: modelData === desktops.currentDesktop
                readonly property bool occupied: windows.count > 0

                Layout.fillHeight: true
                Layout.preferredWidth: dot.width + 10
                hoverEnabled: true
                Accessible.role: Accessible.Button
                Accessible.name: desktops.desktopNames[index] ?? ""
                onClicked: root.kwin("setCurrentDesktop", [new DBus.int32(index + 1)])

                TaskManager.TasksModel {
                    id: windows
                    filterByVirtualDesktop: true
                    virtualDesktop: cell.modelData
                    filterByActivity: true
                    activity: activities.currentActivity
                    groupMode: TaskManager.TasksModel.GroupDisabled
                }

                Rectangle {
                    id: dot
                    anchors.centerIn: parent
                    width: cell.current ? 24 : 8
                    height: 8
                    radius: height / 2
                    color: Kirigami.Theme.textColor
                    opacity: cell.current ? 1 : (cell.occupied ? 0.55 : 0.22) + (cell.containsMouse ? 0.25 : 0)

                    Behavior on width { NumberAnimation { duration: Kirigami.Units.shortDuration } }
                    Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }
                }
            }
        }
    }
}
