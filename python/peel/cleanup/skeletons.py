# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

''' Legacy Code '''

HIPS      = 0
CHEST     = 1
NECK      = 2
HEAD      = 3
CLAVL     = 4
CLAVR     = 5
SHOULDERL = 6
SHOULDERR = 7
ARMROLLL  = 8
ARMROLLR  = 9
ELBOWL    = 10
ELBOWR    = 11
FOREROLLL = 12
FOREROLLR = 13
HANDL     = 14
HANDR     = 15
HIPL      = 16
HIPR      = 17
KNEEL     = 18
KNEER     = 19
FOOTL     = 20
FOOTR     = 21
TOEL      = 22
TOER      = 23
LAST      = 24



class Arena(object) :
    def markers(self) :
        return [
         'Hip1', 'Hip3', 'Hip2', 'Hip4', 'Hip1', 
         'Chest1', 'Chest2', 'Chest3', 
         'Head1', 'Head2', 'Head3', 
         'LUArm1', 'LUArm2', 'LUArm3', 
         'LHand1', 'LHand2', 'LHand3',
         'RUArm1', 'RUArm2', 'RUArm3', 
         'RHand1', 'RHand2', 'RHand3',
         'RShin1', 'RShin2', 'RThigh1', 'RThigh2', 
         'RFoot1', 'RFoot2', 'RFoot3', 'RToes1',
         'LShin1', 'LShin2', 'LThigh1', 'LThigh2', 
         'LFoot1', 'LFoot2', 'LFoot3', 'LToes1' ]


    def lines(self) :

        return [
            [ 'RFoot1', 'RFoot3', 'RFoot2', 'RFoot1', 'RToes1' ],
            [ 'LFoot2', 'LFoot3', 'LFoot1', 'LFoot2', 'LToes1' ],
            [ 'RFoot3', 'RShin2', 'RFoot2' ], 
            [ 'LFoot1', 'LFoot2', 'LShin2', 'LFoot3' ] ,
            [ 'RShin2', 'RShin1', 'RThigh2', 'RThigh1', 'RShin1' ] ,
            [ 'LShin2', 'LShin1', 'LThigh2', 'LThigh1', 'LShin1' ] ,
            [ 'RThigh1', 'Hip2' ] ,
            [ 'LThigh1', 'Hip1' ] ,
            [ 'Hip1', 'Hip3', 'Hip2', 'Hip4', 'Hip1' ] ,
            [ 'Chest1', 'Chest2', 'Chest3', 'Chest1' ] ,
            [ 'Hip4', 'Chest3', 'Chest2', 'Hip4' ] ,
            [ 'Head1', 'Head2', 'Head3', 'Head1'] ,
            [ 'RUArm3', 'RUArm2', 'RUArm1', 'RUArm3' ] ,
            [ 'LUArm3', 'LUArm2', 'LUArm1', 'LUArm3' ] ,
            [ 'LHand1', 'LHand2', 'LHand3', 'LHand1'] ,
            [ 'RHand1', 'RHand2', 'RHand3', 'RHand1'] ,
            [ 'LUArm3', 'Chest1', 'RUArm3' ] ,
            [ 'RUArm1', 'RHand2' ] ,
            [ 'LUArm1', 'LHand2' ] 
        ]



class Motive(object)  :

    def markers(self) :

        return [ 'Hip_1',         'Hip_2',       'Hip_3',      'Hip_4',  
                 'Chest_1',       'Chest_2',     'Chest_3',    'Chest_4',
                 'Head_1',        'Head_2',      'Head_3',
                 'LShoulder_1',   'LShoulder_2', 'LUArm_1',    'LUArm_2', 
                 'LHand_1',       'LHand_2',     'LHand_3',
                 'RShoulder_1',   'RShoulder_2', 'RUArm_1',    'RUArm_2',  
                 'RHand_1',       'RHand_2',     'RHand_3',
                 'LThigh_1',      'LThigh_2',    'LShin_1',    'LShin_2',
                 'LFoot_1',       'LFoot_2',     'LFoot_3',    'LToe_1',
                 'RThigh_1',      'RThigh_2',    'RShin_1',    'RShin_2',   
                 'RFoot_1',       'RFoot_2',     'RFoot_3',    'RToe_1' ]

    def lines(self) :
        return [ 
            [ 'RFoot_1', 'RFoot_3', 'RFoot_2', 'RFoot_1', 'RToe_1' ] ,
            [ 'LFoot_2', 'LFoot_3', 'LFoot_1', 'LFoot_2', 'LToe_1' ] ,
            [ 'RFoot_3', 'RShin_1', 'RFoot_2' ] ,
            [ 'LFoot_1', 'LFoot_2', 'LShin_1', 'LFoot_3' ] ,
            [ 'RShin_1', 'RShin_2', 'RThigh_2', 'RThigh_1', 'RShin_2' ] ,
            [ 'LShin_1', 'LShin_2', 'LThigh_2', 'LThigh_1', 'LShin_2' ] ,
            [ 'RThigh_1', 'Hip_2' ] ,
            [ 'LThigh_1', 'Hip_1' ] ,
            [ 'Hip_1', 'Hip_2', 'Hip_4', 'Hip_3', 'Hip_1' ] ,
            [ 'Chest_1', 'LShoulder_1', 'RShoulder_1', 'Chest_1' ] ,
            [ 'LShoulder_2', 'LShoulder_1', 'Chest_1',  'RShoulder_1',  'RShoulder_2', 'Chest_2', 'LShoulder_2' ] ,
            [ 'Hip_3', 'Chest_3', 'Chest_4', 'Hip_4' ] ,
            [ 'Chest_1', 'Chest_3', 'LShoulder_2' ] ,
            [ 'Chest_1', 'Chest_4', 'RShoulder_2' ] ,
            [ 'Head_1', 'Head_2', 'Head_3', 'Head_1'] ,
            [ 'RShoulder_2', 'RUArm_2', 'RUArm_1' ] ,
            [ 'LShoulder_2', 'LUArm_2', 'LUArm_1' ] ,
            [ 'LHand_1', 'LHand_2', 'LHand_3', 'LHand_1'] ,
            [ 'RHand_1', 'RHand_2', 'RHand_3', 'RHand_1'] ,
            [ 'RUArm_1', 'RHand_2' ] ,
            [ 'LUArm_1', 'LHand_2' ] 
        ]



    def jointMap(self) :

        hw = .7 # hand weight
        fw = 2  # foot weight

        return {

            HIPS       : [ ('Hip_1',   3), ('Hip_2',   3), ('Hip_3',   3),   ('Hip_4',   3) ] ,
            CHEST      : [ ('Chest_1', 2), ('Chest_2', 2), ('Chest_3', 2),   ('Chest_4', 2) ] ,
            BACK       : [ ('Chest_3', 1), ('Chest_4', 1), ('Hip_4',   2),   ('Hip_3',   2) ] ,
            HEAD       : [ ('Head_1',  1), ('Head_2',  1), ('Head_3',  1) ] ,
            NECK       : [ ('LShoulder_2', 1), ('Chest_2', 1), ('RShoulder_2', 1), ('Head_1', 0.5) ] ,
            CLAVR      : [ ('RShoulder_1', 1), ('RShoulder_2', 1) ] ,
            CLAVL      : [ ('LShoulder_1', 1), ('LShoulder_2', 1) ] ,
            SHOULDERR  : [ ('RUArm_1', 4),  ('RUArm_2', 3), ('RShoulder_1', 3), ('RShoulder_2', 3) ] ,
            SHOULDERL  : [ ('LUArm_1', 4),  ('LUArm_2', 3), ('LShoulder_1', 3), ('LShoulder_2', 3) ] ,
            ARMROLLR   : [ ('RUArm_2', 4), ('RUArm_1', hw) ] ,
            ARMROLLL   : [ ('LUArm_2', 4), ('LUArm_1', hw) ] ,
            ELBOWR     : [ ('RUArm_1', hw) ] ,
            ELBOWL     : [ ('LUArm_1', hw) ] ,
            FOREROLLL  : [ ('LHand_2', hw),  ('LHand_3', hw) ] ,
            FOREROLLR  : [ ('RHand_2', hw),  ('RHand_3', hw) ] ,
            HANDR      : [ ('RHand_1', hw),  ('RHand_2', hw), ('RHand_3', hw) ] ,
            HANDL      : [ ('LHand_1', hw),  ('LHand_2', hw), ('LHand_3', hw) ] ,
            THIGHR     : [ ('RThigh_1', 1), ('RThigh_2', 1) ] ,
            THIGHL     : [ ('LThigh_1', 1), ('LThigh_2', 1) ] ,
            KNEER      : [ ('RShin_1', 1),  ('RShin_2', 1) ] ,
            KNEEL      : [ ('LShin_1', 1),  ('LShin_2', 1) ] ,
            FOOTR      : [ ('RFoot_1', fw),  ('RFoot_2', fw), ('RFoot_3', fw)] ,
            FOOTL      : [ ('LFoot_1', fw),  ('LFoot_2', fw), ('LFoot_3', fw)] ,
            TOER       : [ ('RToe_1', 1) ] ,
            TOEL       : [ ('LToe_1', 1) ] 
        }



class Motive37(object) :

    def markers(self) :

        return [ 'Hip_1',         'Hip_2',       'Hip_3',      'Hip_4',  
                 'Chest_1',       'Chest_2',     'Chest_3',    'Chest_4',
                 'Head_1',        'Head_2',      'Head_3',
                 'LShoulder_1',   'LShoulder_2', 'LUArm_1',    'LUArm_2', 
                 'LHand_1',       'LHand_2',     'LHand_3',
                 'RShoulder_1',   'RShoulder_2', 'RUArm_1',    'RUArm_2',  
                 'RHand_1',       'RHand_2',     'RHand_3',
                 'LThigh_1',      'LThigh_2',    'LShin_1',    'LShin_2',
                 'LFoot_1',       'LFoot_2',         
                 'RThigh_1',      'RThigh_2',    'RShin_1',    'RShin_2',   
                 'RFoot_1',       'RFoot_2',      ]


    def lines(self) :

        return [
                [ 'LShin_1', 'LFoot_2', 'LFoot_1', 'LFoot_2'  ],
                [ 'RShin_1', 'RFoot_2', 'RFoot_1', 'RFoot_2'  ],
                [ 'Hip_1', 'Hip_2', 'Hip_4', 'Hip_3', 'Hip_1' ],
                [ 'LHand_1', 'LHand_2', 'LHand_3', 'LHand_1' ],
                [ 'RHand_1', 'RHand_2', 'RHand_3', 'RHand_1' ],
                [ 'Head_1',  'Head_2',  'Head_3',  'Head_1'  ],
                [ 'Chest_4', 'Chest_3', 'LShoulder_2', 'Chest_2', 'RShoulder_2', 'Chest_4'],
                [ 'RShoulder_1', 'Chest_1', 'LShoulder_1', 'RShoulder_1' ],
                [ 'RShin_2',  'RThigh_1', 'RThigh_2', 'RShin_2' ],
                [ 'LShin_2',  'LThigh_1', 'LThigh_2', 'LShin_2' ],
                [ 'LUArm_1',  'LUArm_2',  'LShoulder_2', 'LUArm_1' ],
                [ 'RUArm_1',  'RUArm_2',  'RShoulder_2', 'RUArm_1' ],
                [ 'LUArm_1' , 'LHand_2' ],
                [ 'RUArm_1' , 'RHand_2' ],
                [ 'RShin_2' , 'RShin_1', 'RShin_1' ],
                [ 'LShin_2' , 'LShin_1', 'LShin_1' ],
                [ 'Chest_3',  'Hip_3',  'Hip_4', 'Chest_4' ],
                [ 'LThigh_1', 'Hip_1',  'Hip_2', 'RThigh_1' ],
                [ 'Chest_1', 'Chest_3', 'Chest_4', 'Chest_1' ],
                [ 'LShoulder_1', 'LShoulder_2' ],
                [ 'RShoulder_1', 'RShoulder_2' ],
                [ 'Chest_1', 'Hip_1', 'Hip_2', 'Chest_1' ]
            ]


    def jointMap(self) :

        return {
        
            HIPS       : [ ('Hip_1',   3), ('Hip_2',   3), ('Hip_3',   3),   ('Hip_4',   3) ] ,
            CHEST      : [ ('Chest_1', 2), ('Chest_2', 2), ('Chest_3', 2),   ('Chest_4', 2) ] ,
            BACK       : [ ('Chest_3', 1), ('Chest_4', 1), ('Hip_4',   1),   ('Hip_3',   1) ] ,
            HEAD       : [ ('Head_1',  1), ('Head_2',  1), ('Head_3',  1) ] ,
            NECK       : [ ('LShoulder_2', 1), ('Chest_2', 1), ('RShoulder_2', 1), ('Head_1', 0.5) ] ,
            CLAVR      : [ ('RShoulder_1', 1), ('RShoulder_2', 1) ] ,
            CLAVL      : [ ('LShoulder_1', 1), ('LShoulder_2', 1) ] ,
            SHOULDERR  : [ ('RUArm_1', 4),  ('RUArm_2', 3), ('RShoulder_1', 3), ('RShoulder_2', 3) ] ,
            SHOULDERL  : [ ('LUArm_1', 4),  ('LUArm_2', 3), ('LShoulder_1', 3), ('LShoulder_2', 3) ] ,
            ARMROLLR   : [ ('RUArm_2', 4) ] ,
            ARMROLLL   : [ ('LUArm_2', 4) ] ,
            ELBOWR     : [ ('RHand_2', 1),  ('RHand_3', 1) ] ,
            ELBOWL     : [ ('LHand_2', 1),  ('LHand_3', 1) ] ,
            HANDR      : [ ('RHand_1', 1),  ('RHand_2', 1), ('RHand_3', 1) ] ,
            HANDL      : [ ('LHand_1', 1),  ('LHand_2', 1), ('LHand_3', 1) ] ,
            THIGHR     : [ ('RThigh_1', 1), ('RThigh_2', 1) ] ,
            THIGHL     : [ ('LThigh_1', 1), ('LThigh_2', 1) ] ,
            KNEER      : [ ('RShin_1', 1),  ('RShin_2', 1) ] ,
            KNEEL      : [ ('LShin_1', 1),  ('LShin_2', 1) ] ,
            FOOTR      : [ ('RFoot_1', 2),  ('RFoot_2', 2), ('RShin_1', 2)] ,
            FOOTL      : [ ('LFoot_1', 2),  ('LFoot_2', 2), ('LShin_1', 2)] ,
            TOEL       : [] ,
            TOER       : [] 
        }



class Motive49(object) :

    def markers(self) :
        return [ 'Hip_1',         'Hip_2',       'Hip_3',      'Hip_4',  
                 'Chest_1',       'Chest_2',     'Chest_3',    'Chest_4',
                 'Head_1',        'Head_2',      'Head_3',
                 'LShoulder_1',   'LShoulder_2', 'LUArm_1',    'LUArm_2',  'LFArm_2',
                 'LHand_1',       'LHand_2',     'LHand_3',
                 'LThumb1_1',     'LPinky1_1',   'LIndex1_1' ,
                 'RShoulder_1',   'RShoulder_2', 'RUArm_1',    'RUArm_2',  'RFArm_2',
                 'RHand_1',       'RHand_2',     'RHand_3',
                 'RThumb1_1',     'RPinky1_1',   'RIndex1_1' ,
                 'LThigh_1',      'LThigh_2',    'LShin_1',    'LShin_2',
                 'LFoot_1',       'LFoot_2',     'LFoot_3',    'LToe_1',
                 'RThigh_1',      'RThigh_2',    'RShin_1',    'RShin_2',   
                 'RFoot_1',       'RFoot_2',     'RFoot_3',    'RToe_1' ]

    def lines(self) :
        return [  
            [ 'RFoot_1', 'RFoot_3', 'RFoot_2', 'RFoot_1', 'RToe_1' ] ,
            [ 'LFoot_2', 'LFoot_3', 'LFoot_1', 'LFoot_2', 'LToe_1' ] ,
            [ 'RFoot_3', 'RShin_1', 'RFoot_2' ] ,
            [ 'LFoot_1', 'LFoot_2', 'LShin_1', 'LFoot_3' ] ,
            [ 'RShin_1', 'RShin_2', 'RThigh_2', 'RThigh_1', 'RShin_2' ] ,
            [ 'LShin_1', 'LShin_2', 'LThigh_2', 'LThigh_1', 'LShin_2' ] ,
            [ 'RThigh_1', 'Hip_2' ] ,
            [ 'LThigh_1', 'Hip_1' ] ,
            [ 'Hip_1', 'Hip_2', 'Hip_4', 'Hip_3', 'Hip_1' ] ,
            [ 'Chest_1', 'LShoulder_1', 'RShoulder_1', 'Chest_1' ] ,
            [ 'LShoulder_2', 'LShoulder_1', 'Chest_1',  'RShoulder_1',  'RShoulder_2', 'Chest_2', 'LShoulder_2' ] ,
            [ 'Hip_3', 'Chest_3', 'Chest_4', 'Hip_4' ] ,
            [ 'Chest_1', 'Chest_3', 'LShoulder_2' ] ,
            [ 'Chest_1', 'Chest_4', 'RShoulder_2' ] ,
            [ 'Head_1', 'Head_2', 'Head_3', 'Head_1'] ,
            [ 'RShoulder_2', 'RUArm_2', 'RUArm_1', 'RFArm_2', 'RFArm_1', 'RUArm_1' ] ,
            [ 'LShoulder_2', 'LUArm_2', 'LUArm_1', 'LFArm_2', 'LFArm_1', 'LUArm_1' ] ,
            [ 'LFArm_1', 'LHand_2', 'LPinky1_1', 'LIndex1_1', 'LHand_1', 'LThumb1_1', 'LFArm_1' ] ,
            [ 'LHand_2', 'LHand_1',  'LFArm_1' ] ,
            [ 'RFArm_1', 'RHand_2', 'RPinky1_1', 'RIndex1_1', 'RHand_1', 'RThumb1_1', 'RFArm_1' ] ,
            [ 'RHand_2', 'RHand_1',  'RFArm_1' ] 
        ]
 
