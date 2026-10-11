# Plan for Preparation

## AKA Preliminary Action, Preparatory Stage

Effectively mitigating uncertainties in software development activities might require a comprehensive understanding of task or project elements before delving into detailed activity. For example, a given uncertainty about usability should be considered when developing every user interface that can be affected by it. In some cases, information that can help to better deal with this uncertainty can be obtained from research, measurements, or other sources. A strategic approach becomes especially crucial if the same type of uncertainty is present recurrently in several features or parts of the system.

**How to gather information to better deal with a type of uncertainty that is recurrent in several features of the system?**

- If an uncertainty is connected to the usage of a component of a new technology, all the features that use it might be affected by the same type of uncertainty.
- Gathering information before a task reduces the possibility of surprises appearing during its execution; however, it also costs time and resources.
- When one uncertainty affects several system features, it should be considered in developing each of them.
- A proactive approach to reduce uncertainty prepares the team to handle issues that may appear during activity execution.
- The information needed to reduce the uncertainty for a given activity sometimes can only be obtained through experiments and/or measurements.

Therefore:

**Introduce, before activities that recurrently have an associated uncertainty, a new step to obtain information that can help to reduce this uncertainty.**

To address recurrent uncertainties in several features, this pattern proposes the introduction of a new step before an activity that involves action. By incorporating a Plan for Preparation guideline, teams can collect information that can help to deal with uncertainties when executing the activity.

Several steps need to be considered to implement the guideline of Plan for Preparation effectively. Firstly, the team should identify which information can be useful to reduce the uncertainty in the target type of task. Once the information needed is identified, the next stage involves determining how to obtain this information. This may involve: (a) including a Participation Recommendation; (b) retrieving some additional information about the requirements before an activity; (c) reviewing data from past similar projects; and (d) collecting metrics from the application or the environment.

After identifying the information sources, the new step should be planned and executed whenever an activity has the target uncertainty present. For instance, it might be added to a User Story task list and be included in the "Definition of Done". This might affect the time to execute that task and, consequently, the cost associated with it. It's essential to communicate the purpose and importance of this new activity to the entire team, ensuring everyone understands its role in addressing uncertainties and improving project results.

A recommended approach in implementing this pattern involves incorporating this new step into the project process. It might affect the planning and the definition of done for delivering a feature. Depending on the effort required for the previous step, it might be planned together or done in a separate task. Integrating it becomes useful for teams as it would enable them to effectively localize this step within the project's schedule, thereby increasing the chances of achieving its goal of minimizing uncertainties. Finally, regular review and adjustment of the preemptive action process are necessary to adapt to the changes in the project and the development of uncertainties. This iterative approach allows teams to refine their strategies over time and continuously improve their ability to mitigate uncertainties effectively.

## Consequences

The following are the consequences of using this pattern:

- Reduced uncertainties emerging during the execution of a recurring situation that can appear in several features.
- Provide a standard path to deal with functionalities that face the same type of uncertainty.
- It can affect the definition of done if a new outcome is expected from the task.
- The additional time required for the additional step should be considered in planning.
- Requires additional time to execute the new type of activity, which can also affect the team development speed and increase the overall cost.

## Related Patterns

Bring the Specialist can be used together with Plan for Preparation when some specific knowledge is required for the new task added in the project. An Architectural Spike can be used to explore solutions before adopting this pattern. The software analytics patterns can also be used in this context to obtain the information needed for reducing uncertainty.

## Examples

_For instance, consider an application that receives data from several systems. A recurring uncertainty when implementing functionality with an external integration concerns the data quality of the information received, like if it has missing data or if it is consistent. So, to handle this, the team Plan for Preparation introduced a previous step to analyze a data sample to understand better the problems that should be handled and which corrections are possible. As a result of this activity, the uncertainty when implementing the integration is reduced because the team will know which problems they need to handle._
