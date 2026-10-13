# Architectural Trigger

Agile teams value responding to change over following a plan. It is common to evolve and refine your architecture during development, but the appropriate time to make significant architecture changes isn't always clear. For instance, it can be necessary to implement memory optimization due to performance degradation. Or, refactoring part of the system to introduce a new service or threading model could cause some architectural rework. However, it is not always clear what will lead you to revisit your architecture or when changes will be required.

**How can the team know when to rework or evolve the architecture?**

Premature optimization and premature abstraction can generate unnecessary work and add complexity to future tasks. Attempting to improve some aspect of your design might not have the payoff you expected. However, it is important to keep the architecture in synch with and supportive of emerging requirements.

You want to focus on implementing user functionality while at the same time adequately evolving your architecture. It can be difficult to predict when you need to shift emphasis from implementing functionality to working on improving your architecture. Being aware of architectural considerations is important, however you don't want to waste time worrying over things that might not be relevant.

If certain architectural issues are not addressed in a timely manner, it can be expensive to rework the architecture. Not addressing the architecture regularly can lead to an architecture that is hard to change and to validate.

Therefore:

**Define conditions that trigger architectural investigations which may lead to adding tasks to the backlog.**

The triggers can be based on when values of certain system qualities are not being met. These triggers might be based on criteria established in an **Agile Landing Zone**, or by **Continuous Inspection** tools for code quality conditions, or conditions defined by the team.

**Agile Landing Zones** define acceptable minimal values for system quality attributes. An architecture trigger should be defined for when a landing zone attribute drops below the minimum. The process of **Continuous Inspection** can also reveal parts of the architecture that need attention. It is impossible to predict when these triggers will appear. Whether or not you decide to work on the architecture, however, depends on your diagnosis of why the condition was triggered.

There are different ways to monitor trigger conditions. For example, a team might use a **System Quality Dashboard** or a **System Quality Radiator** to get regular feedback about important system qualities and be notified when a problem is detected. When a triggering condition occurs, the team will need to determine whether there is an easy fix or whether you need to define relevant architectural tasks and prioritize them in the backlog. The technical plan may prescribe options that can be taken in case the trigger is activated and define the tasks that should be added to the backlog.

Some triggering conditions can be hard to quantify. However, there should be an agreement by the team on how to determine when these hard-to-quantify conditions should trigger an architectural task. For instance, a discussion between developers can determine that when an unacceptable number of complexity or code smells are present, they will consider refactoring the code. This trigger can be noted and discussed by the team when someone believes that a triggering condition has been reached.

The architectural trigger should be defined for characteristics that affect the system as a whole and not a single component, class, or isolated function. For instance, if one class is growing too big, that should be considered a design problem. However if a set of related classes in the same layer is growing too big, then it might be considered an architectural issue because it can affect the design integrity of the entire layer. This distinction is important because the introduction of a new cross-cutting architectural feature has a higher impact on the system as a whole than does a change to an isolated class. The actions to be performed when the trigger conditions are met are often hard to precisely define. It may be clear that some specific refactoring should be performed, but the scope of that task may require some investigation before it is added to the backlog. When the path to follow is not clear, the team can use an **Architectural Spike** to investigate appropriate actions to take.

For example, a measurement can be performed frequently to verify if a performance attribute is inside the respective **Agile Landing Zone**. If it is found that the measurement is below the minimum acceptable value, a task to improve the performance should be added in the backlog and considered for the next iteration. You can also define easily implemented micro benchmarks to measure the performance of simple, common system behaviors and trigger further investigation when performance degrades.

---

## Related Patterns

The identification of architecture triggers can be part of the **Plan for Responsible Moments** defined at the beginning of the project. In response to a trigger, an associated action can be added representing **Architecture in the Backlog**.

## Examples

*In the project SADE, for an emergency response system, an architectural trigger was developed for the reverse AJAX mechanism. If measurements reported that it was not fulfilling the performance requirements, an optimization architectural task should be added to the backlog. Despite defining this trigger, the initial solution proved adequate and no additional optimization was required.*

*Platforms such as Mezuro and SonarQ provide support for sending notifications to development teams according to configuration criteria based on the source code metrics. If the metrics value exceeds a configured threshold, the team is notified that they should do something about it. These can be considered architectural triggers for code quality.*
