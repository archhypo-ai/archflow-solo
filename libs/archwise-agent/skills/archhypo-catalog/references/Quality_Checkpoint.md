# Quality Checkpoint

## AKA Verification Barrier, Quality Gate

Sometimes, the possibility that some type of artifact does not possess certain qualities can bring uncertainty to the project. Ensuring that individual artifacts have certain qualities, such as usability or performance, can reduce the impact and level of uncertainty throughout an issue that can affect the entire architecture. For instance, ensuring that each component has its performance within an expected threshold can reduce uncertainty regarding the performance of the entire system. Likewise, ensuring that web pages only rely on a centralized stylesheet for formatting reduces the impact of a more general change in usability. However, warranting a property in some type of artifact for several functionalities is not easy and requires constant effort.

**How to ensure certain quality in each unit of an artifact type that can help to reduce uncertainty or its impact on the entire system?**

- Certain qualities of the software are challenging to predict during the development process.
- Ensuring specific properties in system artifacts can help to handle uncertainties in the whole project.
- Even when a given Protective Guideline is defined by the team, it might not be correctly followed in all the cases.
- Modifying an attribute in several parts of the system can be very time-consuming.

Therefore:

**Introduce a verification activity after the development of an artifact to verify if the desired quality is present, reducing the uncertainty level or its impact regarding that quality in the context of the whole project.**

Considering a documented hypothesis as a starting point, the first step is to identify if ensuring a certain property in individual artifacts or in certain parts of the system can contribute to handling the respective uncertainty as a whole. These artifacts may include code modules, documentation, user interfaces, system configurations, and others. Once the type of artifact is identified, the team must define the quality criteria against which they will be evaluated. For that, clear and measurable standards or specifications must be established for the artifacts to be considered acceptable.

The second implementation stage involves creating a verification task to be performed after the target artifact is created. The project plan should clearly outline this task, emphasizing its significance for the uncertainty management strategy. By explicitly assigning a verification task, teams establish a proactive approach to addressing uncertainties and mitigating potential impacts early in the development process. Depending on the type of verification that needs to be performed, the verification can be automated, such as part of an automated test or based on metrics threshold, or manual, like done by a code review or document inspection. It is important to highlight that this practice goes beyond just creating acceptance or regression testing; it can define a guideline to be considered in current and future tests.

The third stage involves planning and allocating time for the verification task. In the case of automated verification, the implementation of the mechanism needs to be planned once. If the approach is manual, it needs to be planned for each time a new artifact is created or an existing one is changed. This will help ensure the verification is not rushed or ignored, allowing teams to consider the completed activity.

If an artifact fails in the verification, the normal procedure would be to return to it and try to achieve the desired property. However, there might be some cases in which the verification failure is justified. For instance, if a transaction does not reach the desired performance threshold, there might be, in that case, a justified reason for that. In that case, the verification can work as an alert to evaluate how that situation affects the uncertainty on a larger scale. Other alternative strategies may be required to handle the respective hypothesis.

## Examples

_As an example, consider an e-commerce system with millions of users per day, where it was identified the following hypothesis: "Even after a new feature was developed or a new product registered on the database, the time for searching a product must be less than 1 second for the final user". To ensure the desired performance, the team establishes a Quality Checkpoint that every time a new feature is released or new products are registered on the database, it should be confirmed if the search time is still within the desired threshold. That should be done by executing the existing automated tests and creating new ones when needed._

_As another example, in a healthcare system where the target public includes elderly users, an uncertainty was represented by the following hypothesis: "The system has a suitable usability of elderly users." To ensure this experience for elderly users, the team establishes a Quality Checkpoint that should be considered every time a new user interface is created or an existing one receives significant changes. In these cases, a preliminary UX evaluation of the interface should be performed with this target public before proceeding to implementation._

## Consequences

The following are the consequences of using this pattern:

- Verifying each artifact might help reduce uncertainties in the overall project.
- The team will receive early feedback on a given uncertainty, allowing proactive actions.
- In cases where the team judges it is not possible to achieve the desired property, other strategies might be planned in advance.
- This technique might impact project time and resources since an automated verification should be implemented, and manual verifications should be done for each artifact of the target type.
- While ensuring that each part has the desired quality can help to manage the uncertainty, it might bring a false impression that it is enough.

## Related Patterns

Based on measurements obtained in the Quality Checkpoint, the definition of an **Architectural Trigger** can be used to create criteria to trigger a reevaluation of the current solution as a whole. The verification performed in the Quality Checkpoint can also be added in the **Test Architecture** to make sure that this type of verification will be adopted in the appropriate scenarios.
