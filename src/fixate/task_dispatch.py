from threading import Timer
from pubsub import pub
from fixate.sequencer import Sequencer


class TaskDispatcher:
    """
    This class listens on the cmd queue and dispatches the data and commands to the relevant functions.
    It is the main running loop in the software as it receives input from the command queue as well as distributing the
    results.
    """

    def __init__(self):
        self.sequencer = Sequencer()
        self.tick = 0.05
        self.status = "Stopped"
        pub.subscribe(self.process_cmd_queue, 'Command')

    def run(self):
        if self.status == "Running":
            self.sequencer.run_once()
            Timer(self.tick, self.run).start()

    def process_cmd_queue(self, cmd, data):
        # Each command is only successfully processed once
        self.process_sequencer_commands(cmd, data)

    def process_sequencer_commands(self, cmd, data):
        if cmd == "Seq_Start":
            self.sequencer.status = "Running"
            return True
        if cmd == "Seq_Pause":
            self.sequencer.status = "Paused"
            return True
        if cmd == "Seq_Stop":
            self.sequencer.status = "Stopped"
            return True
        if cmd == "Seq_Load_Tests":
            self.sequencer.load(data)
            return True
        if cmd == "Seq_Clear_Tests":
            self.sequencer.clear_tests()
        return False

    def start(self):
        self.status = "Running"

    def stop(self):
        self.status = "Stopped"