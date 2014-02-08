VMThunder
=========
Creating a large number of virtual machine instances in an IaaS
cloud can be quite time-consuming, because the virtual disk
images need to be transferred to the compute nodes in prior to
booting. 

VMThunder addresses this problem by 3 improvements: compute node 
caching, P2P transfering and prefetching, in addition to on-demand 
transfering (network storage). VMThunder is a scalable and cost-effective
accelerator for bulk povisioning of virtual machines. And it can
be, if preferred, gracefully turned off after the booting process is
complete.

Benchmarks show that VMThunder can boot 160 VMs (CentOS 6.2 with
gnome desktop) on 160 compute nodes with in a minute, and
the average time consumption is 20 seconds. With prefetching, the
complete and average time consumption can be respecttively reduced
to 18 and 16 seconds. The network is Gigabit Ethernet for all
servers in the benchmark environment.

Background
============
The Infrastructure as a Service (IaaS) cloud has become
increasingly important due to its flexible pay-as-you-go business 
model. Over the IaaS cloud, customers
can rent computing and storage resources
according to their actual service requirement, and thus
they can save a great deal of cost without the need to
invest on computing infrastructure. The convenience
for customers, however, poses a challenging problem
to IaaS cloud providers: how to accommodate dynamic
computing requirements of customers, who may
request a large quantity of virtual machines (VMs) in
a short time period?

It has been seen that in large-scale IaaS cloud
like the National Supercomputing Center of China
in Tianjin (NSCC-Tianjin), some users require
resources (virtual CPU, memory, disk space) for
compute-intensive applications, including, for example,
animation, DNA sequence analysis, and weather
forecast. In many cases, they may submit requests
for hundreds of VMs and they need the cloud to
respond to their requests quickly. Once their services
finish, they normally release VMs to save cost. The
similar phenomenon has been observed in other commercial
IaaS cloud such as Amazon EC2.
For an IaaS cloud service provider, a large delay in
VM provisioning (e.g., hours) may turn its customers
away to its competitors, and it is thus critical to
support fast provisioning of a large amount of VMs
to maintain its market competence.

Substantial efforts have been devoted to fast provisioning
of a large number of VMs. Nevertheless,
existing solutions still have large room for further
improvement. For example, the time for provisioning
VMs over Amazon EC2 is still non trivial, taking from
3 minutes up to 30 minutes to get a 1 GB compressed
VM image ready to work. Wartel et al. use
the peer-to-peer (P2P) technology to disseminate VM
images, and it takes about 30 minutes to configure 400
servers. Some work focuses on the problem
of optimal image placement. Based on the analysis
of empirical usage of VM images, they split
the images into small strips over the distributed file
system for efficient access and storage. This method,
however, needs a long time to pre-process the image
files. Another type of solutions uses the so-termed
"memory fork" method (e.g., SnowFlock and Twinkle), 
which remotely clones VMs by duplicating
the running states of the VM. Memory fork, however,
may cause new problems such as data persistence.

Though the transferring process can be eliminated by using network
storage like NFS, cluster FS, distributed FS or SAN, this approach
lacks scalability due to the limited number of replica for each piece
of data. Booting a large number of virtual machines will direct a
large number of servers to access the same set of data at the same
time, which will generate great pressure on the storage servers.
What's more, network storage tends to provide less I/O performance
at a reasonable price.

VMThunder pushes the state of the art of largescale VM provisioning, 
by integrating on-demand transferring, compute node (client-side) 
caching, P2P transfering and prefetching. The protocol for data 
transferring is iSCSI, but technically compatible with other 
protocols like nbd, FCoE or AoE. Caching is realized with Facebook's 
flashcache module, but technically compatible with other block-level 
caching modules like bcache, dm-cache, etc.
  
    



