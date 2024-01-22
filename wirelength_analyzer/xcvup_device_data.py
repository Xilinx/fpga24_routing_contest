# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Zak Nafziger, AMD
#
# SPDX-License-Identifier: MIT
#

import re

class xcvupDeviceData:
    """
    This class provides device specific data for the wirelength analyzer.

    The `cells` member provides a dictionary that maps the cell type (e.g.
    LUT1) to a method that determines whether a combinatorial path exists
    between an output BEL pin name and a set of input BEL pin names.

    The `pips` member provides a list of tuples where the first element is a
    regular expression to be matched against a wire name, and the second
    element specifies the wirelength of this wire if a match occurs. The
    intended use is for determining the wirelength of a PIP based on the PIP's
    end wire name.
    """

    def __init__(self):

        # Cell connections are described as sets, first we define an empty set:
        self.empty = set()

        # The 'opposite' of an empty set (a set that contains everything)
        # is also needed so we define a class:
        class UniversalSet:
            def __contains__(self, item):
                return True
        self.universal = UniversalSet()

        self.cells = {
            # sequential
            'FDRE':            self.none_to_none,
            'FDCE':            self.none_to_none,
            'FDSE':            self.none_to_none,
            'FDPE':            self.none_to_none,

            'SRL16E':          self.srl16e,
            'SRLC32E':         self.srlc32e,

            'RAMD32':          self.ram_32,
            'RAMS32':          self.ram_32,

            'RAMD64E':         self.ram_64e,
            'RAMS64E':         self.ram_64e,

            'RAMB36E2':        self.none_to_none,
            'RAMB18E2':        self.none_to_none,
            'FIFO18E2':        self.none_to_none,

            'MMCME4_ADV':      self.none_to_none,

            'URAM288':         self.none_to_none,

            'GTYE4_CHANNEL':   self.none_to_none,
            'GTYE4_COMMON':    self.none_to_none,
            'PCIE40E4':        self.none_to_none,
            'CMACE4':          self.none_to_none,

            'STARTUPE3':       self.none_to_none,
            'ICAPE3':          self.none_to_none,

            # combinatorial
            'LUT1':            self.all_to_all,
            'LUT2':            self.all_to_all,
            'LUT3':            self.all_to_all,
            'LUT4':            self.all_to_all,
            'LUT5':            self.all_to_all,
            'LUT6':            self.all_to_all,

            'CARRY8':          self.carry8,

            'MUXF7':           self.all_to_all,
            'MUXF8':           self.all_to_all,
            'MUXF9':           self.all_to_all,

            'IBUFCTRL':        self.all_to_all,
            'INBUF':           self.all_to_all,
            'OBUFT':           self.all_to_all,
            'DIFFINBUF':       self.all_to_all,
            'IBUFDS_GTE4':     self.all_to_all,

            # The following cell types are BELs that make up a DSP macro.
            # Such DSPs contains a number of optional pipelining registers,
            # but to determine whether such registers are enabled currently
            # requires examining the design's corresponding Logical Netlist.
            # For the purpose of the FPGA24 Routing Contest, we optimistically
            # assume that all BELs possessing a CLK pin are fully sequential.
            'DSP_A_B_DATA':    self.none_to_none,
            'DSP_C_DATA':      self.none_to_none,
            'DSP_M_DATA':      self.none_to_none,
            'DSP_PREADD_DATA': self.none_to_none,
            'DSP_OUTPUT':      self.none_to_none,
            'DSP_ALU':         self.none_to_none,
            'DSP_MULTIPLIER':  self.all_to_all,
            'DSP_PREADD':      self.all_to_all,
        }

        # pip wirelengths are assigned based on the values provided in Table 1
        # of "An Open-source Lightweight Timing Model for RapidWright", Maidee
        # et al, link: https://www.rapidwright.io/docs/_downloads/6610b931d8a2e053e69a499d3923077f/FPT19-TimingModel.pdf
        self.pips =  [
            #intra-tile (zero wirelength)
            # INT tiles
            (re.compile(r'LOGIC_OUTS_[LR]\d{1,2}'),                  0),
            (re.compile(r'INT_NODE_SDQ_\d{1,2}_INT_OUT[01]'),        0),
            (re.compile(r'INT_NODE_IMUX_\d{1,2}_INT_OUT[01]'),       0),
            (re.compile(r'INT_INT_SDQ_\d{1,2}_INT_OUT[01]'),         0),
            (re.compile(r'INT_NODE_GLOBAL_\d{1,2}_INT_OUT[01]'),     0),
            (re.compile(r'IMUX_[EW]\d{1,2}'),                        0),
            (re.compile(r'IMUX(_CMT)?(_XIPHY\d{1,2})?'),             0),
            (re.compile(r'IMUXOUT\d{1,2}'),                          0),
            (re.compile(r'CTRL_[EW][0-9]'),                          0),
            (re.compile(r'CLE_CLE_[LM]_SITE_0_[A-H](_O|MUX|Q(2)?)'), 0),
            (re.compile(r'BYPASS_[EW]\d{1,2}'),                      0),
            (re.compile(r'BOUNCE_[EW]_\d{1,2}_FT[01]'),              0),
            (re.compile(r'INODE_[EW]_\d{1,2}_FT[01]'),               0),
            (re.compile(r'SDQNODE_[EW]_\d{1,2}_FT[01]'),             0),
            # LAG_LAG tiles
            (re.compile(r'LAG_MUX_ATOM_\d{1,2}_TXOUT'),              0),
            (re.compile(r'UBUMP\d{1,2}'),                            0), # In multi-SLR devices, this wire is typically
                                                                         # used to cross the SLR. Since the xcvu3p is
                                                                         # a single SLR device, this wire can only be
                                                                         # used as a 'U-turn' back into the same tile
            (re.compile(r'RXD\d{1,2}'),                              0),

            #single horizontal
            (re.compile(r'[EW]{2}1_[EW]_BEG[0-7]'),                  1),
            (re.compile(r'WW1_E_7_FT0'),                             1),

            #single vertical
            (re.compile(r'[NS]{2}1_[EW]_BEG[0-7]'),                  1),

            #double horizontal
            (re.compile(r'[EW]{2}2_[EW]_BEG[0-7]'),                  5),

            #double vertical
            (re.compile(r'[NS]{2}2_[EW]_BEG[0-7]'),                  3),

            #quad horizontal
            (re.compile(r'[EW]{2}4_[EW]_BEG[0-7]'),                  10),

            #quad vertical
            (re.compile(r'[NS]{2}4_[EW]_BEG[0-7]'),                  5),

            #long horizontal
            (re.compile(r'[EW]{2}12_BEG[0-7]'),                      14),

            #long vertical
            (re.compile(r'[NS]{2}12_BEG[0-7]'),                      12),

            #ignored (static and global routing resources)
            (re.compile(r'VCC_WIRE'),                                0),
            (re.compile(r'GND_WIRE[1-3]'),                           0),
            (re.compile(r'CLK_LEAF_SITES_\d_CLK_LEAF'),              0),
        ]

        # recognized tile types and regex to strip tile location
        self.tile_root_name_regex = re.compile(r'(.+)_X\d+Y\d+')
        self.tile_types = {
            'CLEL_R', 'CLEM', 'CLEM_R', 'BRAM', 'DSP', 'XIPHY_BYTE_L',
            'HPIO_L', 'CMT_L', 'URAM_URAM_FT', 'URAM_URAM_DELAY_FT', 'GTY_L',
            'GTY_R', 'LAG_LAG'
        }

        # bels that drive global nets
        self.global_net_drivers = {
            'BUFCE', 'BUFG_GT', 'BUFG_GT_SYNC'
        }

    def none_to_none(self, o):
        """
        Default connectivity for combinatorial logic

        The set of connections from all inputs to any output is the empty set
        """
        return self.empty

    def all_to_all(self, o):
        """
        Default connectivity for combinatorial logic

        The set of connections from all inputs to any output always contains
        every input
        """
        return self.universal

    def carry8(self, o):
        """
        Connectivity rule for CARRY8 cells
        """
        connectivity = { 'O0':  {'CIN', 'S0'},
                         'CO0': {'CIN', 'S0',       'DI0', 'AX'},
                         'O1':  {'CIN', 'S1', 'S0', 'DI0', 'AX'},
                         'CO1': {'CIN', 'S1',       'DI1', 'BX', 'S0', 'DI0', 'AX'},
                         'O2':  {'CIN', 'S2', 'S1', 'DI1', 'BX', 'S0', 'DI0', 'AX'},
                         'CO2': {'CIN', 'S2',       'DI2', 'CX', 'S1', 'DI1', 'BX', 'S0', 'DI0', 'AX'},
                         'O3':  {'CIN', 'S3', 'S2', 'DI2', 'CX', 'S1', 'DI1', 'BX', 'S0', 'DI0', 'AX'},
                         'CO3': {'CIN', 'S3',       'DI3', 'DX', 'S2', 'DI2', 'CX', 'S1', 'DI1', 'BX', 'S0', 'DI0', 'AX'},
                         'O4':  {'CIN', 'S4'  'S3', 'DI3', 'DX', 'S2', 'DI2', 'CX', 'S1', 'DI1', 'BX', 'S0', 'DI0', 'AX'},
                         'CO4': {'CIN', 'S4',       'DI4', 'EX', 'S3', 'DI3', 'DX', 'S2', 'DI2', 'CX', 'S1', 'DI1', 'BX', 'S0', 'DI0', 'AX'},
                         'O5':  {'CIN', 'S5', 'S4'  'DI4', 'EX', 'S3', 'DI3', 'DX', 'S2', 'DI2', 'CX', 'S1', 'DI1', 'BX', 'S0', 'DI0', 'AX'},
                         'CO5': {'CIN', 'S5',       'DI5', 'FX', 'S4', 'DI4', 'EX', 'S3', 'DI3', 'DX', 'S2', 'DI2', 'CX', 'S1', 'DI1', 'BX', 'S0', 'DI0', 'AX'},
                         'O6':  {'CIN', 'S6', 'S5', 'DI5', 'FX', 'S4'  'DI4', 'EX', 'S3', 'DI3', 'DX', 'S2', 'DI2', 'CX', 'S1', 'DI1', 'BX', 'S0', 'DI0', 'AX'},
                         'CO6': {'CIN', 'S6',       'DI6', 'GX', 'S5', 'DI5', 'FX', 'S4', 'DI4', 'EX', 'S3', 'DI3', 'DX', 'S2', 'DI2', 'CX', 'S1', 'DI1', 'BX', 'S0', 'DI0', 'AX'},
                         'O7':  {'CIN', 'S7', 'S6', 'DI6', 'GX', 'S5', 'DI5', 'FX', 'S4'  'DI4', 'EX', 'S3', 'DI3', 'DX', 'S2', 'DI2', 'CX', 'S1', 'DI1', 'BX', 'S0', 'DI0', 'AX'},
                         'CO7': {'CIN', 'S7',       'DI7', 'HX', 'S6', 'DI6', 'GX', 'S5', 'DI5', 'FX', 'S4', 'DI4', 'EX', 'S3', 'DI3', 'DX', 'S2', 'DI2', 'CX', 'S1', 'DI1', 'BX', 'S0', 'DI0', 'AX'},
                       }
        return connectivity[o]

    def srl16e(self, o):
        """
        Connectivity rule for SRL16E cells
        """
        connectivity = { 'O5': {'A0', 'A1', 'A2', 'A3'},
                         'O6': {'A0', 'A1', 'A2', 'A3'},
                         'MC31': set(),
                        }
        return connectivity[o]

    def srlc32e(self, o):
        """
        Connectivity rule for SRLC32E cells
        """
        connectivity = { 'O6': {'A0', 'A1', 'A2', 'A3', 'A4'},
                         'MC31': set(),
                       }
        return connectivity[o]

    def ram_32(self, o):
        """
        Connectivity rule for RAMS32 and RAMD32 cells
        """
        connectivity = { 'O5': {'A0', 'A1', 'A2', 'A3', 'A4'},
                         'O6': {'A0', 'A1', 'A2', 'A3', 'A4'},
                       }
        return connectivity[o]

    def ram_64e(self, o):
        """
        Connectivity rule for RAMS64E and RAMD64E cells
        """
        connectivity = { 'O6': {'A0', 'A1', 'A2', 'A3', 'A4', 'A5'},
                       }
        return connectivity[o]

