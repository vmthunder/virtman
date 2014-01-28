VMThunder
=========
Creating a large number of virtual machine instances in an IaaS cloud can be quite time-consuming, because the virtual disk images need to be transferred to the compute nodes in prior to booting. 

Though the transferring process can be eliminated by using network storage like NFS, cluster FS, distributed FS or SAN, this approach lacks scalability due to the limited number of replica for each piece of data. Booting a large number of virtual machines will direct a large number of servers to access the same set of data at the same time, which will generate great pressure on the storage servers. What's more, network storage tend to provide less I/O performance at a reasonable price.

VMThunder addresses this problem by introducing compute node caching, P2P transfering and prefetching to the network storage approach, resulting in a scalable and cost-effective accelerator for booting. VMThunder can be, if preferred, gracefully switched off after the booting process is complete.

Benchmarks show that VMThunder can boot 160 VMs (CentOS 6.2 with gnome desktop) on 160 compute nodes in less than 1 minutes, and the average time consumption is 20 seconds. With prefetching, the complete and average time consumption can be reduced to 18 and 16 seconds, respecttively. The network is Gigabit Ethernet for all servers in the benchmark environment.
