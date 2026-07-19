package RiskDrivenMilestone {
	//  Idiomatic SysML v2: the design->requirement->verification relations use NATIVE
	//  constructs (satisfy / verification+verify / VerdictKind); the acquisition-process
	//  relations (assessedAt / informs / tracesToAuthority) have no native SysML equivalent
	//  and stay as RockWorx bridge connections -- that division is the point of the link.
	private import RWXAcqTags::*;
	private import VerificationCases::VerdictKind;

	part def AirVehicle;

	part program {

		//  The design element (the air vehicle being acquired).
		part airVehicle : AirVehicle;

		//  The KPP as a native SysML v2 requirement, tagged as a KeyPerformanceParameter.
		requirement kpp_Thrust {
			@KeyPerformanceParameter {}
		}

		//  Native satisfy: the design satisfies the KPP.
		satisfy kpp_Thrust by airVehicle;

		//  Native verification case: verifies the KPP; recorded verdict = fail.
		verification hotfire_verification {
			objective {
				verify kpp_Thrust;
			}
			attribute riskDisposition = "Open";
			return verdict : VerdictKind = VerdictKind::fail;
		}

		//  Acquisition-process elements (tagged) -- no native SysML relation for these.
		part pdr { @TechnicalReview {} }
		part ms_b { @AcquisitionGate {} }
		part title10_4271 { @AuthorityReference {} }

		//  Acquisition-process bridge connections (no native SysML v2 construct exists).
		connection assessedAt connect kpp_Thrust to pdr;
		connection informs connect pdr to ms_b;
		connection wasDerivedFrom connect kpp_Thrust to title10_4271;
	}
}
