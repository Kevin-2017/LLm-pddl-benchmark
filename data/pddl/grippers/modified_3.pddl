(define (problem gripper_random_3)
    (:domain gripper-strips)
    (:objects
        robot1 robot2 robot3 - robot
room1 room2 - room
ball1 ball2 - object
rgripper1 rgripper2 rgripper3 lgripper1 lgripper2 lgripper3 - gripper
    )
    (:init
        (at-robby robot1 room1)
(at-robby robot2 room1)
(at-robby robot3 room2)
(free robot1 rgripper1)
(free robot1 lgripper1)
(free robot2 rgripper2)
(free robot2 lgripper2)
(free robot3 rgripper3)
(free robot3 lgripper3)
(at ball1 room1)
(at ball2 room2)
    )
    (:goal
        (and
            (at ball1 room1)
(at ball2 room1)
        )
    )
)
