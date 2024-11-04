(define (domain cake)
  (:requirements :strips)
  (:predicates
    (have ?c)
    (eaten ?c)
  )
  (:action eat
      :parameters (?c)
      :precondition (have ?c)
      :effect (and
          (not (have ?c))
          (eaten ?c)
      )
  )
  (:action bake
      :parameters (?c)
      :precondition (and (not (have ?c)))
      :effect (have ?c)
  )
)