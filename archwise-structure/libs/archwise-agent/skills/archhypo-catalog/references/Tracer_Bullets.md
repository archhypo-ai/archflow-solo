# Tracer Bullets

## AKA Walking Skeleton

Despite the architecture being based on a reference, there can be several low-level decisions that should be made, such as what frameworks should be used, how it should be instantiated and configured, and how the architectural layers are going to be organized and connected. These decisions are important to identify in order to define a standard to be followed during the implementation of the remaining system functionality, in order to achieve design consistency.

**How can you define low-level details about the architecture without spending a lot of time upfront on a detailed investigation?**

- A high-level architecture defined by the reference usually does not contain enough detail to start the implementation.
- There are several approaches to instantiate the same reference, and if a standard way to do that is not defined in the beginning of the project, several parallel approaches to do the same thing can be used on the software.
- The integration between the reference and the solutions on the technical plans may not be clear or trivial.
- There are some assumptions in the technical plans that may need to be verified with initial implementations to eliminate some risks at the beginning of the project.
- Once the iterations that deliver value to customers begin, there are more pressures on the team, and the time to explore different solutions becomes more limited.

Therefore:

**Select the smallest set of architecturally relevant user stories and implement them as references for upcoming functionality. Use this implementation to face technical challenges that were planned to be targeted before the project iterations.**

These user stories should implement real user requirements and explore the basic architectural layers. During this implementation the frameworks can be introduced to provide functionality and the team can validate its suitability to the problem. During this implementation, if necessary, several options can be evaluated. After implementing the whole functionality, the code should be reviewed for refactoring opportunities, because it will be used as a reference and even a small problem here has a high potential to be propagated to the whole project.

Other user stories that focus on architecture features need validation at the beginning of the project can also be included when you **Plan Responsible Moments**. These implementations should explore different possibilities and some design or architectural spikes can also be performed to fulfil this task. At the end of this implementation of these stories, the team should take time to evaluate the solution and make sure that "standard ways" of implementing architecture details are identified and understood by all.

The functionality developed by early **Tracer Bullets** should not be definitive. It should represent a viable start from where the application design may evolve. During the iterations, the design reference for the project may evolve, incorporate new ideas and solutions, and every implemented story should be developed in a way that it can be used as a reference for the next one.

## Benefits and Drawbacks

A benefit of this pattern is that it provides a concrete way to design the basic application architecture, and, besides it is not the focus, the implemented story can still add value to the customers. It also provides a way to prove with code the core concepts of the architecture and solutions proposed to some technical challenges.

The main drawback of this pattern may happen when the developers start to struggle with some technical problems, which can take away the focus from business and delay the start of the iterations. The Tracer Bullet should not be considered an opportunity to develop complex frameworks and structures in the beginning of the project.

## Related Patterns

The **Tracer Bullet** can be considered a concrete and more low-level definition of the reference chosen for the **Reference Architecture**. For some technical challenges, especially the ones with high risk and high impact, its validation by the **Tracer Bullets** can be the best way to **Plan Responsible Moments**.

This pattern is related to the practice **Prove with Code** (Agile Architecture 2015), but this pattern provides a concrete way to do that. This pattern is not new, and its first description was made by Hunt & Thomas (1999). This is similar in some ways to a **Walking Skeleton** (Cockburn 2004) although you might implement **Tracer Bullets** as part of the core architecture rather than as a prototype.
