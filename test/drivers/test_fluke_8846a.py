if __name__ == '__main__':
    # for arg in ['vo', 'dc', 'curr', 'ac']:
    # print(match_arg(arg, MODES.keys()))

    x = mode_builder(MODES, {}, 'volt', 'ac', rang=12, res=1)
    print(x)
    x = mode_builder(MODES, {}, 'volt', 'dc', 'hi', 'rat')
    print(x)
    x = mode_builder(MODES, {}, 'temp', 'RTD')
    print(x)
    # mode_builder(MODES, None, "shsfhgd")

    if DMMs:
        FLUKE = visa.instrument(DMMs[0][1])
        with Fluke8846A(FLUKE) as DMM:
            pass
            """
            # dmm = Fluke8846A(FLUKE)
            print("Frequency\n{}".format(dmm.measure('freq')))
            for y in range(5):
                print(dmm.measure())

            print("Volt AC\n{}".format(dmm.measure('volt', 'ac')))
            for y in range(5):
                print(dmm.measure())

            print("Volt DC\n{}".format(dmm.measure('volt')))
            for y in range(5):
                print(dmm.measure())

            print("Curr DC\n{}".format(dmm.measure('curr')))
            for y in range(5):
                print(dmm.measure())

            print("Curr AC\n{}".format(dmm.measure('curr', 'ac')))
            for y in range(5):
                print(dmm.measure())

            print("Res\n{}".format(dmm.measure('res')))
            for y in range(5):
                print(dmm.measure())

            print("4 wire Res\n{}".format(dmm.measure('fres')))
            for y in range(5):
                print(dmm.measure())


                #"""